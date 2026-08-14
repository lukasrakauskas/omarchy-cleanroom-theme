return {
	{
		dir = vim.fn.stdpath("data") .. "/lazy/github-theme",
		name = "github-theme",
		priority = 1000,
	},
	{
		"LazyVim/LazyVim",
		opts = {
			colorscheme = "github_light",
		},
	},
}
