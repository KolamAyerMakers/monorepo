local dap = require("dap")
dap.adapters.python = {
	type = "executable",
	command = "python",
	args = { "-m", "debugpy.adapter" },
}
vim.fn.sign_define("DapBreakpoint", { text = "B", texthl = "", linehl = "", numhl = "" })
dap.configurations.python = {
	{
		-- The first three options are required by nvim-dap
		type = "python", -- the type here established the link to the adapter definition: `dap.adapters.python`
		request = "launch",
		name = "Launch file",

		-- Options below are for debugpy, see https://github.com/microsoft/debugpy/wiki/Debug-configuration-settings for supported options

		program = "${file}", -- This configuration will launch the current file if used.
		pythonPath = function()
			return os.getenv("VIRTUAL_ENV") .. "/bin/python"
		end,
	},
}
local dap_python = require("dap-python")
dap_python.test_runner = "pytest"
dap_python.setup("python")

-- Setup dapui
local dapui = require("dapui")
dapui.setup()

dap.listeners.before.attach.dapui_config = function()
	dapui.open()
end
dap.listeners.before.launch.dapui_config = function()
	dapui.open()
end
dap.listeners.before.event_terminated.dapui_config = function()
	dapui.close()
end
dap.listeners.before.event_exited.dapui_config = function()
	dapui.close()
end

-- Setup virtual text
require("nvim-dap-virtual-text").setup()

-- Add keymaps
vim.keymap.set("n", "<F5>", function()
	require("dap").continue()
end, { desc = "DAP: continue" })
vim.keymap.set("n", "<F6>", function()
	require("dap").terminate()
end, { desc = "DAP: terminate" })
vim.keymap.set("n", "<F10>", function()
	require("dap").step_over()
end, { desc = "DAP: step over" })
vim.keymap.set("n", "<F11>", function()
	require("dap").step_into()
end, { desc = "DAP: step into" })
vim.keymap.set("n", "<F12>", function()
	require("dap").step_out()
end, { desc = "DAP: step out" })
vim.keymap.set("n", "<Leader>b", function()
	require("dap").toggle_breakpoint()
end, { desc = "DAP: toggle breakpoint" })
vim.keymap.set("n", "<Leader>dr", function()
	require("dap").repl.open()
end, { desc = "DAP: open REPL" })
vim.keymap.set("n", "<Leader>dl", function()
	require("dap").run_last()
end, { desc = "DAP: run last" })
vim.keymap.set({ "n", "v" }, "<Leader>dh", function()
	require("dap.ui.widgets").hover()
end, { desc = "DAP: hover" })
vim.keymap.set({ "n", "v" }, "<Leader>dp", function()
	require("dap.ui.widgets").preview()
end, { desc = "DAP: preview" })
vim.keymap.set("n", "<Leader>df", function()
	local widgets = require("dap.ui.widgets")
	widgets.centered_float(widgets.frames)
end, { desc = "DAP: frames" })
vim.keymap.set("n", "<Leader>dS", function()
	local widgets = require("dap.ui.widgets")
	widgets.centered_float(widgets.scopes)
end, { desc = "DAP: scopes" })
