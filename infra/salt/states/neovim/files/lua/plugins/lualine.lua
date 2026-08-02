require("lualine").setup({
	options = {
		theme = "auto",
		section_separators = { left = "", right = "" },
		component_separators = { left = "", right = "" },
	},
	sections = {
		lualine_a = { {
			"mode",
			fmt = function(str)
				return str:sub(1, 1)
			end,
		} },
	},
})
