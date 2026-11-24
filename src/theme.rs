use iced::{color, Color, Theme};

use crate::config::ThemeChoice;

/// Official Rosé Pine palettes (https://rosepinetheme.com) — iced has no built-in.
fn rose_pine_palette(
    background: Color,
    text: Color,
    primary: Color,
    success: Color,
    danger: Color,
) -> Theme {
    Theme::custom(
        "Rose Pine".into(),
        iced::theme::Palette {
            background,
            text,
            primary,
            success,
            danger,
        },
    )
}

/// The palette to draw with: `System` follows the desktop, using the
/// configured light or dark palette; anything else is itself.
pub fn effective(
    choice: ThemeChoice,
    light: ThemeChoice,
    dark: ThemeChoice,
    system_is_dark: bool,
) -> ThemeChoice {
    match choice {
        ThemeChoice::System if system_is_dark => dark,
        ThemeChoice::System => light,
        other => other,
    }
}

pub fn iced_theme(choice: ThemeChoice, dark: bool) -> Theme {
    if let Some(design) = design(choice) {
        return Theme::custom(choice.label().into(), iced::theme::Palette {
            background: design.background, text: design.text, primary: design.accent,
            success: color!(0x72d9b0), danger: color!(0xff9d9d),
        });
    }
    match choice {
        ThemeChoice::System | ThemeChoice::Light | ThemeChoice::Dark => {
            if dark {
                Theme::Dark
            } else {
                Theme::Light
            }
        }
        ThemeChoice::Dracula => Theme::Dracula,
        ThemeChoice::CatppuccinLatte => Theme::CatppuccinLatte,
        ThemeChoice::CatppuccinFrappe => Theme::CatppuccinFrappe,
        ThemeChoice::CatppuccinMacchiato => Theme::CatppuccinMacchiato,
        ThemeChoice::CatppuccinMocha => Theme::CatppuccinMocha,
        ThemeChoice::RosePine => rose_pine_palette(
            color!(0x191724),
            color!(0xe0def4),
            color!(0xc4a7e7),
            color!(0x9ccfd8),
            color!(0xeb6f92),
        ),
        ThemeChoice::RosePineMoon => rose_pine_palette(
            color!(0x232136),
            color!(0xe0def4),
            color!(0xc4a7e7),
            color!(0x9ccfd8),
            color!(0xeb6f92),
        ),
        ThemeChoice::RosePineDawn => rose_pine_palette(
            color!(0xfaf4ed),
            color!(0x575279),
            color!(0x907aa9),
            color!(0x56949f),
            color!(0xb4637a),
        ),
        _ => unreachable!("button themes handled above"),
    }
}

/// Blur behind the translucent picker (macOS only).
pub fn uses_glass() -> bool {
    cfg!(target_os = "macos")
}

pub fn is_dark(choice: ThemeChoice) -> bool {
    if design(choice).is_some() { return true; }
    match choice {
        ThemeChoice::Light | ThemeChoice::CatppuccinLatte | ThemeChoice::RosePineDawn => false,
        ThemeChoice::Dark
        | ThemeChoice::Dracula
        | ThemeChoice::CatppuccinFrappe
        | ThemeChoice::CatppuccinMacchiato
        | ThemeChoice::CatppuccinMocha
        | ThemeChoice::RosePine
        | ThemeChoice::RosePineMoon => true,
        #[cfg(target_os = "macos")]
        ThemeChoice::System => crate::macos::is_dark_appearance(),
        #[cfg(target_os = "linux")]
        ThemeChoice::System => linux_system_is_dark(),
        #[cfg(not(any(target_os = "macos", target_os = "linux")))]
        ThemeChoice::System => false,
        _ => true,
    }
}

#[cfg(target_os = "linux")]
fn linux_system_is_dark() -> bool {
    crate::xkb_custom::gsettings_get("org.gnome.desktop.interface", "color-scheme")
        .map(|s| s.contains("prefer-dark"))
        .unwrap_or(false)
}

pub struct OverlayColors {
    pub panel: Option<Color>,
    pub chip: Color,
    pub chip_text: Color,
    pub selected: Color,
    pub selected_text: Color,
}

pub fn overlay_colors(choice: ThemeChoice, dark: bool, opacity: f32) -> OverlayColors {
    let opacity = opacity.clamp(0.35, 1.0);
    let p = iced_theme(choice, dark).palette();
    let chip = if dark {
        shift(p.background, 0.08)
    } else {
        shift(p.background, -0.06)
    };
    OverlayColors {
        panel: Some(Color {
            a: opacity,
            ..p.background
        }),
        chip,
        chip_text: p.text,
        selected: p.primary,
        selected_text: contrast_text(p.primary),
    }
}

fn shift(c: Color, delta: f32) -> Color {
    Color {
        r: (c.r + delta).clamp(0.0, 1.0),
        g: (c.g + delta).clamp(0.0, 1.0),
        b: (c.b + delta).clamp(0.0, 1.0),
        a: c.a,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn named_themes_map_to_iced() {
        assert!(matches!(
            iced_theme(ThemeChoice::Dracula, true),
            Theme::Dracula
        ));
        assert!(matches!(
            iced_theme(ThemeChoice::CatppuccinMocha, true),
            Theme::CatppuccinMocha
        ));
        assert!(matches!(
            iced_theme(ThemeChoice::CatppuccinLatte, false),
            Theme::CatppuccinLatte
        ));
        assert!(matches!(
            iced_theme(ThemeChoice::Light, false),
            Theme::Light
        ));
        assert!(matches!(iced_theme(ThemeChoice::Dark, true), Theme::Dark));
    }

    #[test]
    fn system_resolves_to_the_configured_palettes() {
        let (l, d) = (ThemeChoice::RosePineDawn, ThemeChoice::CatppuccinMocha);
        assert_eq!(effective(ThemeChoice::System, l, d, false), l);
        assert_eq!(effective(ThemeChoice::System, l, d, true), d);
        // A named choice ignores the system palettes.
        assert_eq!(effective(ThemeChoice::Dracula, l, d, false), ThemeChoice::Dracula);
        assert_eq!(effective(ThemeChoice::Light, l, d, true), ThemeChoice::Light);
    }

    #[test]
    fn glass_is_macos_only() {
        assert_eq!(uses_glass(), cfg!(target_os = "macos"));
    }

    #[test]
    fn dark_classification() {
        assert!(!is_dark(ThemeChoice::Light));
        assert!(!is_dark(ThemeChoice::CatppuccinLatte));
        assert!(!is_dark(ThemeChoice::RosePineDawn));
        assert!(is_dark(ThemeChoice::Dark));
        assert!(is_dark(ThemeChoice::Dracula));
        assert!(is_dark(ThemeChoice::RosePine));
        assert!(is_dark(ThemeChoice::CatppuccinMocha));
    }
}

/// Omarchy's active palette, shared by the picker and settings window.
#[derive(Debug, Clone, PartialEq)]
pub struct DesktopPalette {
    pub background: Color,
    pub foreground: Color,
    accent: Color,
    selection: Color,
    green: Color,
    red: Color,
}

impl DesktopPalette {
    pub fn parse(contents: &str) -> Option<Self> {
        let values: toml::Value = toml::from_str(contents).ok()?;
        let color = |key: &str| -> Option<Color> {
            let hex = values.get(key)?.as_str()?.strip_prefix('#')?;
            if hex.len() != 6 { return None; }
            let rgb = u32::from_str_radix(hex, 16).ok()?;
            Some(Color::from_rgb8((rgb >> 16) as u8, (rgb >> 8) as u8, rgb as u8))
        };
        Some(Self {
            background: color("background")?, foreground: color("foreground")?,
            accent: color("accent")?, selection: color("selection")?,
            green: color("green")?, red: color("red")?,
        })
    }

    pub fn is_dark(&self) -> bool { luminance(self.background) < 0.179 }

    pub fn theme(&self) -> Theme {
        Theme::custom("Desktop appearance".into(), iced::theme::Palette {
            background: self.background, text: self.foreground, primary: self.accent,
            success: self.green, danger: self.red,
        })
    }

    pub fn overlay(&self, opacity: f32) -> OverlayColors {
        OverlayColors {
            panel: Some(Color { a: opacity.clamp(0.35, 1.0), ..self.background }),
            chip: self.selection, chip_text: self.foreground,
            selected: self.accent,
            selected_text: if luminance(self.accent) > 0.179 { Color::BLACK } else { Color::WHITE },
        }
    }
}

fn luminance(color: Color) -> f32 {
    let linear = |c: f32| if c <= 0.04045 { c / 12.92 } else { ((c + 0.055) / 1.055).powf(2.4) };
    0.2126 * linear(color.r) + 0.7152 * linear(color.g) + 0.0722 * linear(color.b)
}

pub fn desktop_palette() -> Option<DesktopPalette> {
    #[cfg(target_os = "linux")]
    if crate::hyprland::is_running() {
        // Read the current path afresh: Omarchy atomically replaces the theme
        // directory when switching. Never retain a symlink's old target.
        let current = dirs::state_dir()?.join("omarchy/current/theme/colors.toml");
        return DesktopPalette::parse(&std::fs::read_to_string(current).ok()?);
    }
    None
}

#[cfg(test)]
mod desktop_tests {
    use super::*;
    const DARK: &str = r##"background = "#060B1E"
foreground = "#ffcead"
accent = "#7d82d9"
selection = "#252e56"
green = "#92a593"
red = "#ED5B5A"
"##;

    #[test]
    fn desktop_colors_reach_both_windows_and_refresh() {
        let dark = DesktopPalette::parse(DARK).unwrap();
        assert_eq!(dark.theme().palette().background, color!(0x060B1E));
        assert_eq!(dark.overlay(0.8).chip_text, color!(0xffcead));
        assert_eq!(dark.overlay(0.8).chip, color!(0x252e56));
        assert_eq!(dark.overlay(0.8).selected, color!(0x7d82d9));
        let light = DesktopPalette::parse(&DARK.replace("#060B1E", "#ffffff").replace("#7d82d9", "#000000")).unwrap();
        assert_ne!(dark, light);
        assert_eq!(light.theme().palette().background, Color::WHITE);
        assert_eq!(light.overlay(1.0).selected_text, Color::WHITE);
        assert_eq!(dark.overlay(1.0).selected_text, Color::BLACK);
    }

    #[test]
    fn incomplete_or_invalid_palette_is_rejected() {
        assert!(DesktopPalette::parse("").is_none());
        assert!(DesktopPalette::parse(&DARK.replace("#060B1E", "#xyzxyz")).is_none());
        assert!(DesktopPalette::parse(&DARK.replace("#060B1E", "#123")).is_none());
    }
}

/// One palette per button design. Surfaces stay quiet so small characters remain readable.
#[derive(Clone, Copy)]
pub struct Design {
    pub background: Color,
    pub surface: Color,
    pub text: Color,
    pub accent: Color,
    pub secondary: Color,
    pub top: Color,
    pub bottom: Color,
    pub ink: Color,
    pub finish: &'static str,
}

pub fn design(choice: ThemeChoice) -> Option<Design> {
    let (bg, surface, accent, secondary, top, bottom, ink, finish) = match choice {
        ThemeChoice::LagoonEnamel => (0x0c2228, 0x14383e, 0x5cf6d1, 0x7ce5eb, 0x5cf6d1, 0x04525e, 0xf5fffc, "Polished enamel"),
        ThemeChoice::CobaltSatin => (0x111d38, 0x1d3155, 0x8bc8ff, 0xa7b8ff, 0x69b8ff, 0x183489, 0xffffff, "Soft satin"),
        ThemeChoice::AuroraGlass => (0x20172f, 0x34264a, 0xd5b0ff, 0x59efd9, 0xe4a6ef, 0x6540aa, 0xffffff, "Iridescent glass · Default"),
        ThemeChoice::TerracottaClay => (0x2e1d1d, 0x4a2c29, 0xffb18e, 0xf39e9b, 0xf8aa82, 0x8f3c36, 0xfff8ee, "Fine matte clay"),
        ThemeChoice::ChampagneMetal => (0x27231b, 0x3e3526, 0xf0d194, 0xc6a05d, 0xfff0c3, 0x7b5e32, 0x302b24, "Brushed aluminium"),
        ThemeChoice::GraphiteGold => (0x191e25, 0x2a3039, 0xffda77, 0x8c98a8, 0x535c68, 0x131922, 0xffda77, "Machined graphite"),
        _ => return None,
    };
    let rgb = |n: u32| Color::from_rgb8((n >> 16) as u8, (n >> 8) as u8, n as u8);
    Some(Design { background: rgb(bg), surface: rgb(surface), text: color!(0xf5f4fa),
        accent: rgb(accent), secondary: rgb(secondary), top: rgb(top), bottom: rgb(bottom), ink: rgb(ink), finish })
}

pub fn contrast_text(color: Color) -> Color {
    if luminance(color) > 0.179 { Color::BLACK } else { Color::WHITE }
}

pub fn gradient(top: Color, bottom: Color) -> iced::Background {
    iced::Gradient::Linear(iced::gradient::Linear::new(iced::Radians(1.1))
        .add_stop(0.0, top).add_stop(1.0, bottom)).into()
}

/// System mode uses the real desktop colors; custom designs are never overridden by them.
pub fn resolved_theme(choice: ThemeChoice, light: ThemeChoice, dark: ThemeChoice,
    desktop: Option<&DesktopPalette>, system_dark: bool) -> Theme {
    if choice == ThemeChoice::System {
        if let Some(palette) = desktop { return palette.theme(); }
    }
    let choice = effective(choice, light, dark, system_dark);
    iced_theme(choice, is_dark(choice))
}

pub fn resolved_overlay(choice: ThemeChoice, light: ThemeChoice, dark: ThemeChoice,
    desktop: Option<&DesktopPalette>, system_dark: bool, opacity: f32) -> OverlayColors {
    if choice == ThemeChoice::System {
        if let Some(palette) = desktop { return palette.overlay(opacity); }
    }
    let choice = effective(choice, light, dark, system_dark);
    overlay_colors(choice, is_dark(choice), opacity)
}

pub fn panel_background(choice: ThemeChoice, base: Color) -> iced::Background {
    match design(choice) {
        Some(d) => gradient(base, Color { a: base.a, ..d.surface }),
        None => base.into(),
    }
}

pub fn selection_background(choice: ThemeChoice, base: Color) -> iced::Background {
    match design(choice) {
        Some(d) => gradient(d.accent, d.secondary),
        None => base.into(),
    }
}

#[cfg(test)]
mod design_tests {
    use super::*;
    #[test]
    fn seven_options_and_aurora_default_reach_both_windows() {
        assert_eq!(ThemeChoice::ALL.len(), 7);
        assert_eq!(crate::config::Config::default().theme_parsed(), ThemeChoice::AuroraGlass);
        for choice in ThemeChoice::ALL.into_iter().filter(|c| *c != ThemeChoice::System) {
            let d = design(choice).unwrap();
            let theme = resolved_theme(choice, ThemeChoice::Light, ThemeChoice::Dark, None, false);
            let overlay = resolved_overlay(choice, ThemeChoice::Light, ThemeChoice::Dark, None, false, 0.9);
            assert_eq!(theme.palette().primary, d.accent);
            assert_eq!(overlay.selected, d.accent);
            assert!(luminance(d.text) > luminance(d.background));
            // Both ends of a selected-chip gradient must retain readable text.
            for bg in [d.accent, d.secondary] {
                let (a, b) = (luminance(bg), luminance(overlay.selected_text));
                assert!((a.max(b) + 0.05) / (a.min(b) + 0.05) >= 4.5, "{}", choice);
            }
        }
    }
    #[test]
    fn desktop_palette_only_overrides_system_and_updates_live() {
        let mut desktop = DesktopPalette { background: Color::BLACK, foreground: Color::WHITE,
            accent: color!(0x99ddff), selection: color!(0x333333), green: Color::WHITE, red: Color::WHITE };
        let custom = || resolved_theme(ThemeChoice::AuroraGlass, ThemeChoice::Light, ThemeChoice::Dark, Some(&desktop), false);
        assert_eq!(custom().palette().primary, design(ThemeChoice::AuroraGlass).unwrap().accent);
        assert_eq!(resolved_overlay(ThemeChoice::AuroraGlass, ThemeChoice::Light, ThemeChoice::Dark, Some(&desktop), false, 1.0).selected, design(ThemeChoice::AuroraGlass).unwrap().accent);
        for accent in [color!(0x99ddff), color!(0xffaacc)] {
            desktop.accent = accent;
            assert_eq!(resolved_theme(ThemeChoice::System, ThemeChoice::Light, ThemeChoice::Dark, Some(&desktop), false).palette().primary, accent);
            assert_eq!(resolved_overlay(ThemeChoice::System, ThemeChoice::Light, ThemeChoice::Dark, Some(&desktop), false, 1.0).selected, accent);
        }
    }
}


/// Cache the exact artwork rather than re-creating approximate swatches in Settings.
pub fn icon(choice: ThemeChoice) -> Option<iced::widget::image::Handle> {
    use iced::widget::image::Handle;
    use std::sync::OnceLock;
    static ICONS: OnceLock<[Handle; 6]> = OnceLock::new();
    let index = match choice {
        ThemeChoice::LagoonEnamel => 0, ThemeChoice::CobaltSatin => 1,
        ThemeChoice::AuroraGlass => 2, ThemeChoice::TerracottaClay => 3,
        ThemeChoice::ChampagneMetal => 4, ThemeChoice::GraphiteGold => 5,
        _ => return None,
    };
    let icons = ICONS.get_or_init(|| [
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/lagoon-enamel.rgba").to_vec()),
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/cobalt-satin.rgba").to_vec()),
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/aurora-glass.rgba").to_vec()),
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/terracotta-clay.rgba").to_vec()),
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/champagne-metal.rgba").to_vec()),
        Handle::from_rgba(128, 128, include_bytes!("../assets/themes/graphite-gold.rgba").to_vec()),
    ]);
    Some(icons[index].clone())
}
