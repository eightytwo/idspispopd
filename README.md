# idspispopd

A static website generator for my own site, otherwise known as the _Infernal Digital Static Publishing Instrument Simply Producing Orderly Printed Documents_.

## Features

* Blog posts with tags
* Projects listing page
* Markdown support for content (blog posts and projects)
* [Jinja](https://jinja.palletsprojects.com) templates for layout

## Website structure

There are three different groups of files which make up the website.
1. Static files - the CSS, JavaScript, and image files.
2. Templates - these are [Jinja](https://jinja.palletsprojects.com) templates.
3. Content files - blog posts and projects.

The following is the structure of my website and the builder code has constant variables indicating where each group lives on the filesystem.

```
.
├── content
│   ├── blog
│   │   └── 20200701_my_first_post.md
│   └── projects
│       └── walking_through_walls.md
├── static
│   ├── css
│   │   └── style.css
│   ├── images
│   │   └── logo.svg
│   └── index.html
└── templates
    ├── about.html
    ├── base.html
    ├── blog.html
    ├── post.html
    └── projects.html
```

## Building the website

First ensure the requirements are installed. Use a Python 'virtual environment'
if desired - the example below uses the `venv` module of Python 3.

```sh
$ python3 -m venv env
$ . env/bin/activate
(env) $ pip install -r requirements.txt
```

Then, with the static files, content, and templates in place, building the
website is as simple as running:

```sh
(env) $ python3 build.py
```

A `build` directory will be created with the following structure.

```
build
├── about.html
├── blog
│   ├── tag
│   │   └── python.html
│   └── my-first-post.html
├── blog.html
├── css
│   └── style.css
├── images
│   └── logo.svg
├── index.html
└── projects.html
```

The content of the `build` directory can then be copied to a web server.

## What's next?

My website is pretty simple so at this stage there's no plans for anything else. A couple of things that crossed my mind while building this were:
* Tags for projects - might be helpful if the project list grows.
* Individual pages for each project - might be helpful if a particular project has a lot of content.
