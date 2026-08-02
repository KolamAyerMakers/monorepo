require("neotest").setup({
	adapters = {
		require("neotest-python")({
			dap = { justMyCode = false },
		}),
	},
})

-- Setup keymaps
vim.keymap.set("n", "<silent>[f", function()
	require("neotest").jump.prev({ status = "failed" })
end, { desc = "Jump to the previous failed test" })
vim.keymap.set("n", "<silent>]f", function()
	require("neotest").jump.next({ status = "failed" })
end, { desc = "Jump to the next failed test" })
vim.keymap.set("n", "<leader>ts", function()
	require("neotest").summary.toggle()
end, { desc = "Toggle [t]ests [s]ummary" })
vim.keymap.set("n", "<leader>tp", function()
	require("neotest").output_panel.toggle()
end, { desc = "Toggle [t]ests output [p]anel" })
vim.keymap.set("n", "<leader>tw", function()
	require("neotest").watch.toggle(vim.fn.expand("%"))
end, { desc = "[w]atch [t]ests in the current file" })
vim.keymap.set("n", "<leader>ta", function()
	local neotest = require("neotest")
	neotest.run.run(vim.fn.getcwd())
	neotest.summary.open()
end, { noremap = true, desc = "Run [a]ll [t]ests" })
vim.keymap.set("n", "<leader>td", function()
	require("neotest").run.run({ strategy = "dap" })
end, { noremap = true, desc = "[d]ebug [t]est with DAP" })
vim.keymap.set("n", "<leader>tr", function()
	require("neotest").run.run()
end, { noremap = true, desc = "[r]un closest [t]est" })
vim.keymap.set("n", "<leader>tf", function()
	require("neotest").run.run(vim.fn.expand("%"))
end, { noremap = true, desc = "Run [t]est [f]ile" })
