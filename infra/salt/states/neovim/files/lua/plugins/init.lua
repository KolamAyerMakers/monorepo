local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
	local lazyrepo = "https://github.com/folke/lazy.nvim.git"
	vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
end ---@diagnostic disable-next-line: undefined-field
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
	"tpope/vim-sleuth",
	{ "numToStr/Comment.nvim", opts = {} },
	{
		"lewis6991/gitsigns.nvim",
		config = function()
			require("plugins.gitsigns")
		end,
	},
	{
		"folke/which-key.nvim",
		event = "VimEnter",
		opts = {},
	},
	{
		"nvim-telescope/telescope.nvim",
		event = "VimEnter",
		dependencies = {
			"nvim-lua/plenary.nvim",
			{
				"nvim-telescope/telescope-fzf-native.nvim",
				build = "make",
				cond = function()
					return vim.fn.executable("make") == 1
				end,
			},
			{ "nvim-telescope/telescope-ui-select.nvim" },
			{ "nvim-tree/nvim-web-devicons" },
		},
		config = function()
			require("plugins.telescope")
		end,
	},
	{
		"neovim/nvim-lspconfig",
		dependencies = {
			"williamboman/mason.nvim",
			"williamboman/mason-lspconfig.nvim",
			"WhoIsSethDaniel/mason-tool-installer.nvim",
			{ "j-hui/fidget.nvim", opts = {} },
			{ "folke/neodev.nvim", opts = {} },
		},
		config = function()
			require("plugins.lspconfig")
		end,
	},
	{ -- Autocompletion
		"hrsh7th/nvim-cmp",
		event = "InsertEnter",
		dependencies = {
			{
				"L3MON4D3/LuaSnip",
				build = "make install_jsregexp",
				dependencies = {
					{
						"rafamadriz/friendly-snippets",
						config = function()
							require("luasnip.loaders.from_vscode").lazy_load()
						end,
					},
				},
			},
			"saadparwaiz1/cmp_luasnip",
			"hrsh7th/cmp-nvim-lsp",
			"hrsh7th/cmp-path",
		},
		config = function()
			require("plugins.cmp")
		end,
	},
	{ -- Autoformat
		"stevearc/conform.nvim",
		lazy = false,
		keys = {
			{
				"<leader>F",
				function()
					require("conform").format({ async = true, lsp_fallback = true })
				end,
				mode = "",
				desc = "[F]ormat buffer",
			},
		},
		opts = {
			notify_on_error = true,
			format_on_save = function(bufnr)
				-- Disable "format_on_save lsp_fallback" for languages that don't
				-- have a well standardized coding style. You can add additional
				-- languages here or re-enable it for the disabled ones.
				local disable_filetypes = { c = true, cpp = true }
				return {
					timeout_ms = 500,
					lsp_fallback = not disable_filetypes[vim.bo[bufnr].filetype],
				}
			end,
			formatters_by_ft = {
				lua = { "stylua" },
				python = {
					"ruff_fix", -- To fix lint errors.
					"ruff_format", -- To run the Ruff formatter.
				},
				typescript = { "prettier" },
			},
		},
	},
	-- Highlight todo, notes, etc in comments
	{
		"folke/todo-comments.nvim",
		event = "VimEnter",
		dependencies = { "nvim-lua/plenary.nvim" },
		opts = { signs = false },
	},
	-- Collection of various small independent plugins/modules
	{
		"nvim-mini/mini.nvim",
		config = function()
			require("plugins.mini")
		end,
	},
	{ -- Highlight, edit, and navigate code
		"nvim-treesitter/nvim-treesitter",
		build = ":TSUpdate",
		opts = {
			ensure_installed = {
				"bash",
				"c",
				"cpp",
				"cmake",
				"css",
				"dockerfile",
				"gitattributes",
				"gitignore",
				"go",
				"gomod",
				"gosum",
				"gotmpl",
				"gowork",
				"graphql",
				"html",
				"javascript",
				"jq",
				"json",
				"lua",
				"luadoc",
				"make",
				"markdown",
				"python",
				"rst",
				"rust",
				"toml",
				"typescript",
				"vim",
				"vimdoc",
				"yaml",
			},
			auto_install = true,
		},
		config = function(_, opts)
			require("nvim-treesitter").setup(opts)
		end,
	},
	{ "vmware-archive/salt-vim" },
	{
		"rebelot/kanagawa.nvim",
		priority = 1000,
		lazy = false,
		config = function()
			require("kanagawa").setup({
				dimInactive = true,
				theme = "dragon",
			})
			vim.cmd.colorscheme("kanagawa")
		end,
	},
	{
		"nvim-lualine/lualine.nvim",
		dependencies = {
			"catppuccin/nvim",
			"kyazdani42/nvim-web-devicons",
		},
		config = function()
			require("plugins.lualine")
		end,
	},
	{
		"akinsho/toggleterm.nvim",
		version = "*",
		config = function()
			require("plugins.toggleterm")
		end,
	},
	{
		"tpope/vim-fugitive",
		config = function()
			require("plugins.fugitive")
		end,
	},
	{ "j-hui/fidget.nvim", opts = {} },
	{
		"zbirenbaum/copilot.lua",
		cmd = "Copilot",
		event = "InsertEnter",
		config = function()
			require("plugins.copilot")
		end,
	},
	{
		"hedyhli/outline.nvim",
		lazy = true,
		cmd = { "Outline", "OutlineOpen" },
		keys = {
			{ "<leader>O", "<cmd>Outline<CR>", desc = "Toggle outline" },
		},
		opts = {},
	},
	{
		"andythigpen/nvim-coverage",
		dependencies = { "nvim-lua/plenary.nvim" },
		config = function()
			require("plugins.coverage")
		end,
	},
	{
		"mawkler/refjump.nvim",
		keys = { "]r", "[r" },
		opts = {},
	},
})
