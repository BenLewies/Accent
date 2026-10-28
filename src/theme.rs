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
    }
}

/// Blur behind the translucent picker (macOS only).
pub fn uses_glass() -> bool {
    cfg!(target_os = "macos")
}

pub fn is_dark(choice: ThemeChoice) -> bool {
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
        selected_text: color!(0xFFFFFF),
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
    background: Color,
    foreground: Color,
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
