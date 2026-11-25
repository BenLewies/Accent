//! Permission-free Hyprland input backend. The compositor owns the physical
//! devices; Accent uses input-method-v2 and a same-client virtual keyboard.
//! Disconnecting releases the grab, so a crashed daemon cannot strand input.
use crate::config::Config;
use crate::mappings::MappingKey;
use crate::state_machine::{Action, GrabEvent, KeyEvt, KeyInput, ReleaseAction, StateMachine};
use std::collections::{HashMap, HashSet};
use std::io::{Read, Seek, SeekFrom, Write};
use std::os::fd::{AsFd, AsRawFd, FromRawFd};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use tokio::sync::mpsc::UnboundedSender;
use wayland_client::protocol::{wl_registry, wl_seat};
use wayland_client::{Connection, Dispatch, QueueHandle};
use wayland_protocols_misc::zwp_input_method_v2::client::{
    zwp_input_method_keyboard_grab_v2::{self, ZwpInputMethodKeyboardGrabV2},
    zwp_input_method_manager_v2::ZwpInputMethodManagerV2,
    zwp_input_method_v2::{self, ZwpInputMethodV2},
};
use wayland_protocols_misc::zwp_virtual_keyboard_v1::client::{
    zwp_virtual_keyboard_manager_v1::ZwpVirtualKeyboardManagerV1,
    zwp_virtual_keyboard_v1::ZwpVirtualKeyboardV1,
};
use xkbcommon::xkb;

static READY: AtomicBool = AtomicBool::new(false);
static SELECTED: AtomicBool = AtomicBool::new(false);
static ERROR: Mutex<String> = Mutex::new(String::new());
struct ReadinessGuard;
impl Drop for ReadinessGuard {
    fn drop(&mut self) { READY.store(false, Ordering::Relaxed); }
}
pub fn select(value: bool) { SELECTED.store(value, Ordering::Relaxed); }
pub fn selected() -> bool { SELECTED.load(Ordering::Relaxed) }
pub fn is_ready() -> bool { READY.load(Ordering::Relaxed) }
pub fn error() -> String { ERROR.lock().unwrap().clone() }

struct Input {
    seat: Option<wl_seat::WlSeat>,
    manager: Option<ZwpInputMethodManagerV2>,
    vk_manager: Option<ZwpVirtualKeyboardManagerV1>,
    keyboard: Option<ZwpVirtualKeyboardV1>,
    text_keyboard: Option<ZwpVirtualKeyboardV1>,
    source: Option<xkb::State>,
    output: Option<xkb::State>,
    sm: StateMachine,
    down: HashSet<u16>,
    pending: HashMap<u16, ReleaseAction>,
    tx: UnboundedSender<GrabEvent>,
    failed: Option<String>,
    time: u32,
    private: bool,
}
impl Input {
    fn new(config: &Config, tx: UnboundedSender<GrabEvent>) -> Self {
        Self { seat: None, manager: None, vk_manager: None, keyboard: None,
            text_keyboard: None, source: None, output: None,
            sm: StateMachine::new(config.input_time_ms, config.hold_delay_ms, config.activation_key_parsed()),
            down: HashSet::new(), pending: HashMap::new(), tx, failed: None, time: 0, private: false }
    }
    fn shift(&self) -> bool { self.down.contains(&42) || self.down.contains(&54) }
    fn nonshift(&self) -> bool { [29, 97, 56, 100, 125, 126].iter().any(|c| self.down.contains(c)) }
    fn notify(&self, event: GrabEvent) {
        if matches!(event, GrabEvent::ShowOverlay { .. }) {
            crate::app::set_overlay_placement(crate::x11_layout::focused_window_placement().map(|p| crate::app::Anchor {
                x: p.rect.x, y: p.rect.y, width: p.rect.width, height: p.rect.height, scale: p.scale,
            }));
        }
        let _ = self.tx.send(event);
    }
    fn emit(&mut self, events: &[KeyEvt]) {
        let (Some(keyboard), Some(state)) = (&self.keyboard, &mut self.output) else { return };
        for &event in events {
            let direction = if event.value() == 1 { xkb::KeyDirection::Down } else { xkb::KeyDirection::Up };
            state.update_key((event.code() as u32 + 8).into(), direction);
            // Match a physical keyboard: key first, updated modifiers second.
            keyboard.key(self.time, event.code() as u32, event.value() as u32);
            keyboard.modifiers(state.serialize_mods(xkb::STATE_MODS_DEPRESSED),
                state.serialize_mods(xkb::STATE_MODS_LATCHED), state.serialize_mods(xkb::STATE_MODS_LOCKED),
                state.serialize_layout(xkb::STATE_LAYOUT_EFFECTIVE));
        }
    }
    fn inject(&mut self, text: &str) -> Result<(), String> {
        let keyboard = self.text_keyboard.as_ref().ok_or("No text keyboard")?;
        let (map, codes) = unicode_keymap(text)?;
        send_keymap(keyboard, map.as_bytes())?;
        keyboard.modifiers(0, 0, 0, 0);
        for code in codes {
            keyboard.key(self.time, code, 1);
            keyboard.key(self.time, code, 0);
        }
        // The forwarding keyboard retains its own keymap and modifier state.
        // The compositor switches back on the next forwarded event.
        Ok(())
    }
    fn execute(&mut self, action: Action) {
        self.emit(&action.emit);
        self.pending.extend(action.pending);
        if let Some(text) = action.inject {
            if let Err(error) = self.inject(&text) { self.failed = Some(error); }
        }
        if let Some(event) = action.ui { self.notify(event); }
    }
    fn key(&mut self, code: u16, pressed: bool) {
        crate::grab::apply_live(&mut self.sm);
        let shift_before = self.shift();
        if pressed { self.down.insert(code); } else { self.down.remove(&code); }
        if !pressed {
            if let Some(action) = self.pending.remove(&code) {
                if action == ReleaseAction::EmitVirtualRelease { self.emit(&[KeyEvt::Release(code)]); }
                return;
            }
        }
        if matches!(code, 42 | 54) {
            self.emit(&[if pressed { KeyEvt::Press(code) } else { KeyEvt::Release(code) }]);
            if self.shift() != shift_before {
                if let Some(event) = self.sm.update_shift(self.shift()) { self.notify(event); }
            }
            return;
        }
        let input = self.source.as_ref().map(|s| input_for_code(&s.get_keymap(), code,
            s.serialize_layout(xkb::STATE_LAYOUT_EFFECTIVE))).unwrap_or(KeyInput::Other);
        // Password/PIN fields always receive ordinary typing.
        if self.private { self.sm.force_reset(); }
        let action = if pressed && !self.private {
            self.sm.deferred_press(input, Some(code), self.shift(), self.nonshift())
        } else if !pressed && !self.private {
            self.sm.deferred_release(Some(code), self.shift())
        } else { Action::default() };
        let suppress = action.suppress;
        self.execute(action);
        if !suppress { self.emit(&[if pressed { KeyEvt::Press(code) } else { KeyEvt::Release(code) }]); }
    }
}

/// Unicode is sent with a private virtual-keyboard keymap. This covers every
/// script without changing the user's layout or using the clipboard.
fn unicode_keymap(text: &str) -> Result<(String, Vec<u32>), String> {
    let chars: Vec<char> = text.chars().collect();
    if chars.is_empty() || chars.len() > 240 { return Err("Invalid character sequence".into()); }
    let mut map = String::from("xkb_keymap { xkb_keycodes \"accent\" { minimum = 8; maximum = 255; ");
    for (i, _) in chars.iter().enumerate() { map.push_str(&format!("<K{i:03}> = {}; ", i + 9)); }
    map.push_str("}; xkb_types \"accent\" { type \"ONE_LEVEL\" { modifiers = None; map[None] = Level1; level_name[Level1] = \"Any\"; }; }; xkb_compatibility \"accent\" {}; xkb_symbols \"accent\" { ");
    for (i, ch) in chars.iter().enumerate() { map.push_str(&format!("key <K{i:03}> {{ type=\"ONE_LEVEL\", [ U{:04X} ] }}; ", *ch as u32)); }
    map.push_str("}; };\0");
    Ok((map, (1..=chars.len() as u32).collect()))
}
fn send_keymap(keyboard: &ZwpVirtualKeyboardV1, data: &[u8]) -> Result<(), String> {
    // SAFETY: a constant NUL-terminated name; ownership transfers to File.
    let fd = unsafe { libc::memfd_create(c"accent-keymap".as_ptr(), libc::MFD_CLOEXEC) };
    if fd < 0 { return Err(std::io::Error::last_os_error().to_string()); }
    let mut file = unsafe { std::fs::File::from_raw_fd(fd) };
    file.write_all(data).map_err(|e| e.to_string())?;
    file.seek(SeekFrom::Start(0)).map_err(|e| e.to_string())?;
    keyboard.keymap(1, file.as_fd(), data.len() as u32);
    Ok(())
}
fn input_for_code(map: &xkb::Keymap, code: u16, group: u32) -> KeyInput {
    match code { 57 => return KeyInput::Space, 105 => return KeyInput::LeftArrow,
        106 => return KeyInput::RightArrow, 103 => return KeyInput::UpArrow,
        108 => return KeyInput::DownArrow, 1 => return KeyInput::Escape, _ => {} }
    let key = (code as u32 + 8).into();
    let symbols = map.key_get_syms_by_level(key, group, 0);
    let Some(symbol) = symbols.first() else { return KeyInput::Other };
    let Some(ch) = char::from_u32(xkb::keysym_to_utf32(*symbol)) else { return KeyInput::Other };
    let mapping = crate::xkb_map::letter_from_name(&ch.to_string()).or_else(|| Some(match ch {
        '0' => MappingKey::Num0, '1' => MappingKey::Num1, '2' => MappingKey::Num2,
        '3' => MappingKey::Num3, '4' => MappingKey::Num4, '5' => MappingKey::Num5,
        '6' => MappingKey::Num6, '7' => MappingKey::Num7, '8' => MappingKey::Num8,
        '9' => MappingKey::Num9, ',' => MappingKey::Comma, '.' => MappingKey::Period,
        '-' => MappingKey::Minus, '=' | '+' => MappingKey::Plus, '/' => MappingKey::Slash,
        '\\' => MappingKey::Backslash, '*' => MappingKey::Multiply, '\'' => MappingKey::Quote,
        _ => return None,
    }));
    mapping.map(KeyInput::Letter).unwrap_or(KeyInput::Other)
}

impl Dispatch<wl_registry::WlRegistry, ()> for Input {
    fn event(state: &mut Self, registry: &wl_registry::WlRegistry, event: wl_registry::Event, _: &(), _: &Connection, qh: &QueueHandle<Self>) {
        if let wl_registry::Event::Global { name, interface, version } = event {
            match interface.as_str() {
                "wl_seat" if state.seat.is_none() => state.seat = Some(registry.bind(name, version.min(7), qh, ())),
                "zwp_input_method_manager_v2" => state.manager = Some(registry.bind(name, 1, qh, ())),
                "zwp_virtual_keyboard_manager_v1" => state.vk_manager = Some(registry.bind(name, 1, qh, ())),
                _ => {}
            }
        }
    }
}
impl Dispatch<ZwpInputMethodV2, ()> for Input {
    fn event(state: &mut Self, _: &ZwpInputMethodV2, event: zwp_input_method_v2::Event, _: &(), _: &Connection, _: &QueueHandle<Self>) {
        match event {
            zwp_input_method_v2::Event::Unavailable => state.failed = Some("Another input method is already using this seat. Accent did not replace it.".into()),
            zwp_input_method_v2::Event::ContentType { purpose, hint } => {
                let purpose: u32 = purpose.into();
                let hint: u32 = hint.into();
                state.private = matches!(purpose, 8 | 9) || hint & 0xc0 != 0; // text-input-v3 password / PIN
            }
            zwp_input_method_v2::Event::Deactivate => { state.private = false; state.sm.force_reset(); state.notify(GrabEvent::HideOverlay); }
            _ => {}
        }
    }
}
impl Dispatch<ZwpInputMethodKeyboardGrabV2, ()> for Input {
    fn event(state: &mut Self, _: &ZwpInputMethodKeyboardGrabV2, event: zwp_input_method_keyboard_grab_v2::Event, _: &(), _: &Connection, _: &QueueHandle<Self>) {
        match event {
            zwp_input_method_keyboard_grab_v2::Event::Keymap { format, fd, size } => {
                if u32::from(format) != 1 || size == 0 || size > 16 * 1024 * 1024 { state.failed = Some("Unsupported compositor keymap".into()); return; }
                let mut bytes = Vec::new();
                if std::fs::File::from(fd).take(size as u64).read_to_end(&mut bytes).is_err() { state.failed = Some("Could not read compositor keymap".into()); return; }
                let Ok(text) = String::from_utf8(bytes.clone()) else { state.failed = Some("Invalid compositor keymap".into()); return; };
                let ctx = xkb::Context::new(xkb::CONTEXT_NO_FLAGS);
                let Some(map) = xkb::Keymap::new_from_string(&ctx, text.trim_end_matches('\0').to_string(), xkb::KEYMAP_FORMAT_TEXT_V1, xkb::KEYMAP_COMPILE_NO_FLAGS) else { state.failed = Some("Could not compile compositor keymap".into()); return; };
                if let Some(keyboard) = &state.keyboard {
                    if let Err(error) = send_keymap(keyboard, &bytes) { state.failed = Some(error); return; }
                }
                state.source = Some(xkb::State::new(&map));
                state.output = Some(xkb::State::new(&map));
                READY.store(true, Ordering::Relaxed);
            }
            zwp_input_method_keyboard_grab_v2::Event::Key { time, key, state: key_state, .. } => {
                state.time = time;
                if key <= u16::MAX as u32 { state.key(key as u16, u32::from(key_state) == 1); }
            }
            zwp_input_method_keyboard_grab_v2::Event::Modifiers { mods_depressed, mods_latched, mods_locked, group, .. } => {
                if let Some(source) = &mut state.source { source.update_mask(mods_depressed, mods_latched, mods_locked, 0, 0, group); }
                if let (Some(output), Some(keyboard)) = (&mut state.output, &state.keyboard) {
                    // Keep lock/layout changes, preserving modifiers actually forwarded.
                    let depressed = output.serialize_mods(xkb::STATE_MODS_DEPRESSED);
                    output.update_mask(depressed, mods_latched, mods_locked, 0, 0, group);
                    keyboard.modifiers(depressed, mods_latched, mods_locked, group);
                }
            }
            _ => {}
        }
    }
}
wayland_client::delegate_noop!(Input: ignore wl_seat::WlSeat);
wayland_client::delegate_noop!(Input: ignore ZwpInputMethodManagerV2);
wayland_client::delegate_noop!(Input: ignore ZwpVirtualKeyboardManagerV1);
wayland_client::delegate_noop!(Input: ignore ZwpVirtualKeyboardV1);

fn connect(connection: Connection, config: &Config, tx: UnboundedSender<GrabEvent>) -> Result<(Connection, wayland_client::EventQueue<Input>, Input), String> {
    let mut queue = connection.new_event_queue();
    connection.display().get_registry(&queue.handle(), ());
    let mut input = Input::new(config, tx);
    queue.roundtrip(&mut input).map_err(|e| e.to_string())?;
    if input.seat.is_none() || input.manager.is_none() || input.vk_manager.is_none() {
        return Err("This compositor does not provide input-method-v2 and virtual-keyboard-v1".into());
    }
    Ok((connection, queue, input))
}
pub fn probe() -> Result<(), String> {
    let (tx, _) = tokio::sync::mpsc::unbounded_channel();
    connect(Connection::connect_to_env().map_err(|e| e.to_string())?, &Config::default(), tx)?;
    println!("Hyprland keyboard protocols available; no device permissions required.");
    Ok(())
}
pub fn start(tx: UnboundedSender<GrabEvent>, config: &Config) -> Result<(), String> {
    crate::grab::set_live(config.input_time_ms, config.hold_delay_ms, config.activation_key_parsed());
    // Connect before the GUI switches to XWayland and removes WAYLAND_DISPLAY.
    let connection = Connection::connect_to_env().map_err(|e| e.to_string())?;
    let config = config.clone();
    std::thread::Builder::new().name("accent-wayland-input".into()).spawn(move || {
        let _readiness = ReadinessGuard;
        let result = (|| -> Result<(), String> {
            let (connection, mut queue, mut input) = connect(connection, &config, tx)?;
            let qh = queue.handle();
            let seat = input.seat.as_ref().unwrap();
            let manager = input.vk_manager.as_ref().unwrap();
            input.keyboard = Some(manager.create_virtual_keyboard(seat, &qh, ()));
            input.text_keyboard = Some(manager.create_virtual_keyboard(seat, &qh, ()));
            let method = input.manager.as_ref().unwrap().get_input_method(seat, &qh, ());
            queue.roundtrip(&mut input).map_err(|e| e.to_string())?;
            if let Some(error) = input.failed.take() { return Err(error); }
            let _grab = method.grab_keyboard(&qh, ());
            connection.flush().map_err(|e| e.to_string())?;
            loop {
                queue.dispatch_pending(&mut input).map_err(|e| e.to_string())?;
                if let Some(error) = input.failed.take() { return Err(error); }
                crate::grab::apply_live(&mut input.sm);
                if let Some(event) = input.sm.long_press_tick(input.shift()) { input.notify(event); }
                connection.flush().map_err(|e| e.to_string())?;
                let Some(guard) = connection.prepare_read() else { continue };
                let mut fd = libc::pollfd { fd: guard.connection_fd().as_raw_fd(), events: libc::POLLIN, revents: 0 };
                let timeout = input.sm.long_press_wait_ms();
                // SAFETY: fd refers to a live connection and pollfd is valid for this call.
                let result = unsafe { libc::poll(&mut fd, 1, timeout) };
                if result < 0 {
                    if std::io::Error::last_os_error().kind() == std::io::ErrorKind::Interrupted { continue; }
                    return Err(std::io::Error::last_os_error().to_string());
                }
                if result > 0 { guard.read().map_err(|e| e.to_string())?; }
            }
        })();
        READY.store(false, Ordering::Relaxed);
        if let Err(error) = result { eprintln!("[Accent] Wayland input: {error}"); *ERROR.lock().unwrap() = error; }
        // All protocol objects and the connection drop here, releasing input.
    }).map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unicode_keymap_types_all_scripts_and_sequences_without_a_clipboard() {
        let (text, codes) = unicode_keymap("éÁ€Ꭰ𐒰a\u{301}").unwrap();
        let ctx = xkb::Context::new(xkb::CONTEXT_NO_FLAGS);
        let map = xkb::Keymap::new_from_string(&ctx, text.trim_end_matches('\0').to_string(), xkb::KEYMAP_FORMAT_TEXT_V1, xkb::KEYMAP_COMPILE_NO_FLAGS).unwrap();
        let state = xkb::State::new(&map);
        let actual: String = codes.iter().map(|c| state.key_get_utf8((*c + 8).into())).collect();
        assert_eq!(actual, "éÁ€Ꭰ𐒰a\u{301}");
    }
    #[test]
    fn unicode_map_bounds_and_untrusted_characters() {
        assert!(unicode_keymap("").is_err());
        assert!(unicode_keymap(&"a".repeat(241)).is_err());
        let (map, _) = unicode_keymap("\";\\{}").unwrap();
        assert!(!map.contains("[ \""));
    }
    #[test]
    fn logical_keys_follow_the_supplied_compositor_layout() {
        let ctx = xkb::Context::new(xkb::CONTEXT_NO_FLAGS);
        let map = xkb::Keymap::new_from_names(&ctx, "", "", "fr", "", None, xkb::KEYMAP_COMPILE_NO_FLAGS).unwrap();
        assert_eq!(input_for_code(&map, 16, 0), KeyInput::Letter(MappingKey::A));
        assert_eq!(input_for_code(&map, 30, 0), KeyInput::Letter(MappingKey::Q));
    }
}
