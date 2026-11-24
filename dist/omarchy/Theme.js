.pragma library

// Only bundled names may become image paths. Config values are never URLs.
var designs = ["lagoon-enamel", "cobalt-satin", "aurora-glass",
               "terracotta-clay", "champagne-metal", "graphite-gold"]

function fromConfig(contents) {
    var match = String(contents).match(/^\s*theme\s*=\s*["']([^"'\r\n]*)["']\s*(?:#.*)?$/m)
    var name = match ? match[1].toLowerCase() : "aurora-glass"
    if (name === "system" || designs.indexOf(name) !== -1) return name
    // Keep older explicitly configured desktop palettes usable after upgrading.
    if (["light", "dark", "dracula", "catppuccin-latte", "catppuccin-frappe",
         "catppuccin-macchiato", "catppuccin-mocha", "rose-pine", "rose-pine-moon",
         "rose-pine-dawn"].indexOf(name) !== -1) return "system"
    return "aurora-glass"
}

function plain(value) {
    return String(value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}
