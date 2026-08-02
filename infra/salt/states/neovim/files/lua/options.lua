-- Always show status line, even when only 1 buffer is opened
vim.opt.laststatus = 2
-- Drop 'vi' compatibility
vim.opt.compatible = false
-- No backup nor swap files
vim.opt.backup = false
vim.opt.writebackup = false
-- Tabs are 4 characters wide
vim.opt.tabstop = 4
-- Indentation size is 4 characters
vim.opt.shiftwidth = 4
-- Tabs are converted to spaces
vim.opt.expandtab = true
-- Hide buffers when they are abandoned
vim.opt.hidden = true
-- Display the cursor position on the bottom right corner
vim.opt.ruler = true
-- Allow backspace, space, and arrow keys to wrap lines
vim.opt.whichwrap = "b,s,<,>,[,]"
-- Display line numbers
vim.opt.number = true
-- Use relative line numbering
vim.opt.relativenumber = true
-- Quickly display matching paren/bracket when typing
vim.opt.showmatch = true
-- Display --INSERT-- or --REPLACE-- in status line
vim.opt.showmode = false
-- Enable mouse
vim.opt.mouse = "a"
-- Define places where backspace is allowed to remove a character
vim.opt.backspace = "indent,eol,start"
-- Highlight the current line background
vim.opt.cursorline = true
-- Highlight at 80 characters
vim.opt.colorcolumn = "80"
-- Wrap long lines by default
vim.opt.wrap = true
-- Enable incremental search
vim.opt.incsearch = true
-- Enable search highlighting
vim.opt.hlsearch = true
-- Do smart case matching
vim.opt.smartcase = true
-- Start scrolling 5 lines before the window border
vim.opt.scrolloff = 5
-- Show commands
vim.opt.showcmd = true
-- turn on wild menu :e <Tab>
vim.opt.wildmenu = true
-- set wildmenu to list choice
vim.opt.wildmode = "list:longest"
-- Highlight trailing spaces, and tabs
vim.opt.list = true
vim.opt.listchars = "trail:•,nbsp:•,tab:>•"
-- Configure vim to render on a dark background
vim.opt.background = "dark"
-- Update swap file after 300ms
vim.opt.updatetime = 300
-- Always show the signcolumn, otherwise it would shift the text each time
-- diagnostics appear/become resolved.
vim.opt.signcolumn = "yes"
-- Enable 24-bit RGB colors
vim.opt.termguicolors = true
-- Sync clipboard between OS and Neovim.
vim.opt.clipboard = "unnamedplus"
-- Enable break indent
vim.opt.breakindent = true
-- Save undo history
vim.opt.undofile = true
-- Map leader key to key ' '
vim.g.mapleader = " "
