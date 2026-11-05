"""Integration checks for Cleanroom with the installed Omarchy 4.5 pipeline.

Requires Python 3.11+, Omarchy 4.5, Neovim, and Aether v3 already installed.
No plugins are downloaded, and all generated state is confined to a temporary HOME.
"""

import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
OMARCHY = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
AETHER = Path(os.environ.get("AETHER_PATH", Path.home() / ".local/share/nvim/lazy/aether"))


class ThemeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (OMARCHY / "bin/omarchy-theme-set-templates", AETHER / "lua/aether/init.lua"):
            if not path.is_file():
                raise RuntimeError(f"Missing test dependency: {path}")
        cls.temp = tempfile.TemporaryDirectory(prefix="cleanroom-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.home = Path(cls.temp.name)
        cls.theme = cls.home / ".local/state/omarchy/current/next-theme"
        cls.theme.mkdir(parents=True)
        # Model the Git-installed theme boundary: no Lua or executable terminal configs.
        for path in ROOT.iterdir():
            if (path.is_file() and path.name != "vscode.json"
                    and path.suffix in {".toml", ".json", ".theme", ".mode"}):
                shutil.copy2(path, cls.theme / path.name)
        cls.env = dict(os.environ, HOME=str(cls.home), OMARCHY_PATH=str(OMARCHY))
        for name, directory in (("CONFIG", ".config"), ("DATA", ".local/share"),
                                ("STATE", ".local/state"), ("CACHE", ".cache")):
            cls.env[f"XDG_{name}_HOME"] = str(cls.home / directory)
        cls.env["PATH"] = str(OMARCHY / "bin") + os.pathsep + cls.env["PATH"]
        subprocess.run([str(OMARCHY / "bin/omarchy-theme-set-templates")],
                       env=cls.env, check=True, capture_output=True, text=True, timeout=20)
        cls.palette = tomllib.loads((ROOT / "colors.toml").read_text())
        script = cls.home / "inspect.lua"
        output = cls.home / "highlights.json"
        script.write_text('''
local ok, err = xpcall(function()
  vim.opt.runtimepath:prepend(vim.env.CLEANROOM_AETHER)
  local spec = dofile(vim.env.CLEANROOM_SPEC)
  require("aether").setup(spec[1].opts)
  vim.cmd.colorscheme(spec[2].opts.colorscheme)
  local result = { colorscheme = vim.g.colors_name, highlights = {} }
  for _, name in ipairs({"Normal", "Comment", "Function", "@keyword", "String",
      "Number", "Constant", "CursorLineNr", "MatchParen", "Visual", "VisualNOS",
      "Search", "IncSearch", "CurSearch", "Character", "GitSignsAdd", "healthSuccess"}) do
    result.highlights[name] = vim.api.nvim_get_hl(0, {name = name, link = false})
  end
  vim.fn.writefile({vim.json.encode(result)}, vim.env.CLEANROOM_OUTPUT)
end, debug.traceback)
if not ok then
  io.stderr:write(err .. "\\n")
  vim.cmd.cquit(1)
end
vim.cmd.qa()
''')
        subprocess.run(["nvim", "--headless", "-u", "NONE", "-i", "NONE", "-n", "-l", str(script)],
                       env=dict(cls.env, CLEANROOM_AETHER=str(AETHER),
                                CLEANROOM_SPEC=str(cls.theme / "neovim.lua"),
                                CLEANROOM_OUTPUT=str(output)),
                       check=True, capture_output=True, text=True, timeout=20)
        cls.nvim = json.loads(output.read_text())

    def test_github_light_syntax(self):
        # Catches palette assignments that leave Aether's stock syntax colors in place.
        expected = {"Function": "#6f42c1", "@keyword": "#d73a49", "String": "#22863a",
                    "Number": "#005cc5", "Constant": "#005cc5", "Comment": "#6a737d"}
        self.assertEqual(self.nvim["colorscheme"], "aether")
        for group, color in expected.items():
            with self.subTest(group=group):
                self.assertEqual(self.nvim["highlights"][group]["fg"], int(color[1:], 16))

    def test_green_status_highlights(self):
        for group in ("Character", "GitSignsAdd", "healthSuccess"):
            with self.subTest(group=group):
                self.assertEqual(self.nvim["highlights"][group]["fg"], 0x22863A)
        pi = json.loads((self.theme / "pi.json").read_text())
        self.assertEqual(pi["vars"][pi["colors"]["success"]], "#22863a")
        claude = json.loads((self.theme / "claude.json").read_text())
        self.assertEqual(claude["overrides"]["success"], "#22863a")

    def test_blue_active_controls(self):
        for group in ("CursorLineNr", "MatchParen"):
            with self.subTest(group=group):
                self.assertEqual(self.nvim["highlights"][group]["fg"], 0x005CC5)
        self.assertEqual(self.nvim["highlights"]["CurSearch"]["bg"], 0x005CC5)

    def test_yellow_visual_selection_on_white_canvas(self):
        self.assertEqual(self.nvim["highlights"]["Normal"]["bg"], 0xFFFFFF)
        self.assertEqual(self.nvim["highlights"]["Normal"]["fg"], 0x000000)
        for group in ("Visual", "VisualNOS"):
            with self.subTest(group=group):
                self.assertEqual(self.nvim["highlights"][group]["bg"], 0xFED442)
        self.assertEqual(self.palette["selection_foreground"], "#000000")

    def test_terminal_generation(self):
        ghostty = (self.theme / "ghostty.conf").read_text()
        self.assertIn("background = #ffffff", ghostty)
        self.assertIn("selection-background = #fed442", ghostty)
        self.assertIn("selection-foreground = #000000", ghostty)
        alacritty = tomllib.loads((self.theme / "alacritty.toml").read_text())
        self.assertEqual(alacritty["colors"]["primary"]["background"], "#ffffff")
        self.assertEqual(alacritty["colors"]["selection"]["background"], "#fed442")
        kitty = (self.theme / "kitty.conf").read_text()
        self.assertIn("active_tab_background #005cc5", kitty)
        foot = configparser.ConfigParser()
        foot.read(self.theme / "foot.ini")
        self.assertEqual(foot["colors-dark"]["background"], "ffffff")

    def test_app_primary_accents(self):
        pi = json.loads((self.theme / "pi.json").read_text())
        self.assertEqual(pi["vars"][pi["colors"]["accent"]], "#005cc5")
        claude = json.loads((self.theme / "claude.json").read_text())
        for name in ("claude", "promptBorder", "bashBorder", "planMode"):
            with self.subTest(name=name):
                self.assertEqual(claude["overrides"][name], "#005cc5")
        btop = (self.theme / "btop.theme").read_text()
        self.assertIn('theme[hi_fg]="#005cc5"', btop)
        self.assertIn('theme[selected_bg]="#fed442"', btop)
        self.assertIn('theme[temp_mid]="#e36209"', btop)
        self.assertIn('theme[mem_box]="#22863a"', btop)

    def test_no_unresolved_templates_or_invalid_data(self):
        for path in self.theme.iterdir():
            with self.subTest(file=path.name):
                content = path.read_text()
                self.assertNotIn("{{", content)
                if path.suffix == ".json":
                    json.loads(content)
                elif path.suffix == ".toml":
                    tomllib.loads(content)

    def test_legacy_palette_consumers_agree(self):
        # Explicit legacy aliases must agree with generated modern terminal palettes.
        pairs = {0: "background", 1: "red", 2: "green", 3: "yellow", 4: "blue",
                 5: "magenta", 6: "cyan", 7: "foreground", 8: "muted", 9: "bright_red",
                 10: "bright_green", 11: "bright_yellow", 12: "bright_blue",
                 13: "bright_magenta", 14: "bright_cyan", 15: "bright_foreground"}
        for slot, key in pairs.items():
            with self.subTest(slot=slot):
                self.assertEqual(self.palette[f"color{slot}"], self.palette[key])


if __name__ == "__main__":
    unittest.main()
