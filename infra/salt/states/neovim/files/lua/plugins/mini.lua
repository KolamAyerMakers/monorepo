-- Better Around/Inside textobjects
--
-- Examples:
--  - va)  - [V]isually select [A]round [)]paren
--  - yinq - [Y]ank [I]nside [N]ext [']quote
--  - ci'  - [C]hange [I]nside [']quote
require("mini.ai").setup({ n_lines = 500 })

-- Add/delete/replace surroundings (brackets, quotes, etc.)
--
-- - saiw) - [S]urround [A]dd [I]nner [W]ord [)]Paren
-- - sd'   - [S]urround [D]elete [']quotes
-- - sr)'  - [S]urround [R]eplace [)] [']
require("mini.surround").setup()

-- Tabline
require("mini.tabline").setup()

-- Auto pairing
require("mini.pairs").setup()

-- Draw indent vertical lines
local indentscope = require("mini.indentscope")
indentscope.setup({
	symbol = "▎",
	draw = { animation = indentscope.gen_animation.none() },
})

-- improved netrw
require("mini.files").setup()
