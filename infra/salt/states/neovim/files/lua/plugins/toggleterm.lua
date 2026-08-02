require("toggleterm").setup()

vim.api.nvim_create_autocmd("TermOpen", {
	pattern = "term://*",
	callback = function()
		-- Hide line numbers
		vim.opt.number = false
		vim.opt.relativenumber = false
		-- Use Esc to leave terminal mode
		vim.keymap.set("t", "<Esc>", "<C-\\><C-n>", { desc = "Exit from terminal mode" })
		-- Toggle terminal with C-t
		vim.keymap.set("t", "<C-t>", "<cmd>ToggleTerm<cr>")
	end,
})

vim.keymap.set("n", "<C-t>", "<cmd>ToggleTerm direction=float<cr>", { desc = "Toggle [t]erminal in float layout" })
vim.keymap.set("n", "<Leader>Tt", "<cmd>ToggleTerm direction=tab<cr>", { desc = "Toggle [T]erminal in [t]ab layout" })
vim.keymap.set(
	"n",
	"<Leader>Th",
	"<cmd>ToggleTerm direction=horizontal<cr>",
	{ desc = "Toggle [T]erminal in [h]orizontal layout" }
)
