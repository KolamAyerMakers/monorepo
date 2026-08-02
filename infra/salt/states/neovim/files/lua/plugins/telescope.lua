require("telescope").setup({
	pickers = {
		colorscheme = {
			enable_preview = true,
		},
	},
	extensions = {
		["ui-select"] = {
			require("telescope.themes").get_dropdown(),
		},
	},
})

-- Enable Telescope extensions if they are installed
pcall(require("telescope").load_extension, "fzf")
pcall(require("telescope").load_extension, "ui-select")

local builtin = require("telescope.builtin")

vim.keymap.set("n", "<leader>ff", builtin.find_files, { desc = "[f]ind [f]iles" })
vim.keymap.set("n", "<leader>lg", builtin.live_grep, { desc = "[l]ive [g]rep" })
vim.keymap.set("n", "<leader>fb", builtin.buffers, { desc = "[f]ind [b]uffer" })
vim.keymap.set("n", "<leader>ht", builtin.help_tags, { desc = "[h]elp [t]ags" })
vim.keymap.set("n", "<leader>?", builtin.keymaps, { desc = "Show keymaps" })
vim.keymap.set("n", "<leader>jl", builtin.jumplist, { desc = "Show [j]ump [l]ist" })
vim.keymap.set("n", "<leader>mp", builtin.man_pages, { desc = "Search [m]an [p]ages" })
vim.keymap.set("n", "<leader>of", builtin.oldfiles, { desc = "Open an [o]ld [f]ile" })
vim.keymap.set("n", "<leader>re", builtin.registers, { desc = "Show [re]gisters" })
vim.keymap.set("n", "<leader>ma", builtin.marks, { desc = "Show [ma]rks" })
vim.keymap.set("n", "<leader>qh", builtin.quickfixhistory, { desc = "Open [q]uickfix history" })
vim.keymap.set("n", "<leader>qp", builtin.quickfix, { desc = "Open [q]uickfix [p]review" })
vim.keymap.set("n", "<leader>ss", builtin.builtin, { desc = "[S]earch [S]elect Telescope" })
vim.keymap.set("n", "<leader>sw", builtin.grep_string, { desc = "[S]earch current [W]ord" })
vim.keymap.set("n", "<leader>sd", builtin.diagnostics, { desc = "[S]earch [D]iagnostics" })
vim.keymap.set("n", "<leader>sr", builtin.resume, { desc = "[S]earch [R]esume" })

vim.keymap.set("n", "<leader>/", function()
	-- You can pass additional configuration to Telescope to change the theme, layout, etc.
	builtin.current_buffer_fuzzy_find(require("telescope.themes").get_dropdown({
		winblend = 10,
		previewer = false,
	}))
end, { desc = "[/] Fuzzily search in current buffer" })
