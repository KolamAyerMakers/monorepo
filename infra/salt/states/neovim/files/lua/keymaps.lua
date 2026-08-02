-- colonless entrance into command mode
vim.keymap.set("n", "!", ":!")
-- Show current buffer file path (because we use <C-G> for gp.nvim)
vim.keymap.set("n", "<C-I>", ":echo expand('%:p')<CR>", { desc = "Show current buffer file path" })
-- Use emacs-style bindings in command mode
vim.keymap.set("c", "<C-A>", "<Home>")
vim.keymap.set("c", "<C-D>", "<Delete>")
vim.keymap.set("c", "<M-Left>", "<S-Left>")
vim.keymap.set("c", "<M-Right>", "<S-Right>")
vim.keymap.set("c", "<C-P>", '<C-R>"')
vim.keymap.set("c", "<S-Ins>", '<C-R>"')
-- Keep the screen centered when moving
vim.keymap.set("n", "<c-d>", "<c-d>zz", { noremap = true })
vim.keymap.set("n", "<c-u>", "<c-u>zz", { noremap = true })
vim.keymap.set("n", "n", "nzzzv", { noremap = true })
vim.keymap.set("n", "N", "Nzzzv", { noremap = true })
-- Move selected lines in visual mode
vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv", { desc = "Move selected line down" })
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv", { desc = "Move selected line up" })
-- location list shortcuts
vim.keymap.set("n", "<leader>lo", ":lopen<CR><C-W><C-W>", { desc = "[l]ocation [o]pen" })
vim.keymap.set("n", "<leader>lc", ":lclose<CR>", { desc = "[l]ocation [c]lose" })
vim.keymap.set("n", "]l", ":lnext<CR>", { desc = "Next [l]ocation" })
vim.keymap.set("n", "[l", ":lprev<CR>", { desc = "Previous [l]ocation" })
-- quickfix list shortcuts
vim.keymap.set("n", "<leader>qo", ":copen<CR><C-W><C-W>", { desc = "[q]uickfix [o]pen" })
vim.keymap.set("n", "<leader>qc", ":cclose<CR>", { desc = "[q]uickfix [c]lose" })
vim.keymap.set("n", "]q", ":cnext<CR>", { desc = "Next [q]uickfix" })
vim.keymap.set("n", "[q", ":cprev<CR>", { desc = "Previous [q]uickfix" })
-- diagnostic
vim.keymap.set("n", "<leader>dl", vim.diagnostic.setloclist, { desc = "Push [d]iagnostics to [l]ocation list" })
vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, { desc = "Go to previous [D]iagnostic message" })
vim.keymap.set("n", "]d", vim.diagnostic.goto_next, { desc = "Go to next [D]iagnostic message" })
-- edit file in same directory
vim.keymap.set("n", "<leader>es", ":e %:h/<CR>", { desc = "[e]dit file in [s]ame directory as buffer (sibling file)" })
-- netrw
vim.api.nvim_create_autocmd("filetype", {
	pattern = "netrw",
	desc = "Better mappings for netrw",
	callback = function()
		local bind = function(lhs, rhs)
			vim.keymap.set("n", lhs, rhs, { remap = true, buffer = true })
		end
		bind("n", "%") -- edit new file
		bind("r", "R") -- rename file
	end,
})
vim.keymap.set("n", "<leader>e.", ":Lexplore<CR>", { desc = "Open [e]xplorer in current directory [.]" })
vim.keymap.set(
	"n",
	"<leader>e%",
	":Lexplore %:h<CR><CR>",
	{ desc = "Open [e]xplorer in current buffer parent directory [%]" }
)
-- Clear incremental search when pressing escape
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")
-- Exit terminal mode
vim.keymap.set("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" })
-- Keybinds to make split navigation easier.
vim.keymap.set("n", "<C-h>", "<C-w><C-h>", { desc = "Move focus to the left window" })
vim.keymap.set("n", "<C-l>", "<C-w><C-l>", { desc = "Move focus to the right window" })
vim.keymap.set("n", "<C-j>", "<C-w><C-j>", { desc = "Move focus to the lower window" })
vim.keymap.set("n", "<C-k>", "<C-w><C-k>", { desc = "Move focus to the upper window" })
