import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from os.path import isfile
from os.path import join
from pathlib import Path
from shutil import copytree
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import markdown
from jinja2 import Environment
from jinja2 import FileSystemLoader
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from slugify import slugify


@dataclass(frozen=True)
class Page:
    category: str
    template: str
    listing: bool = False
    create_detail_pages: bool = False
    detail_page_template: Optional[str] = None
    source_dir: Optional[str] = None


BUILD_PATH = 'build'
STATIC_ASSETS_PATH = 'static'
TEMPLATES_PATH = 'templates'

PAGES = [
    Page(category='404', template='404'),
    Page(category='about', template='about'),
    Page(
        category='blog',
        template='blog',
        listing=True,
        create_detail_pages=True,
        detail_page_template='post',
        source_dir='content/blog',
    ),
    Page(
        category='projects',
        template='projects',
        listing=True,
        source_dir='content/projects',
    ),
]


def write_file(name: str, content: str):
    """Write an HTML file to disk.

    :param name: The name of the file, excluding extension.
    :param content: The content of the file.
    """
    filepath = Path(f'{BUILD_PATH}/{name}.html')
    with open(filepath, "w+", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)


def parse_markdown(filepath: str) -> Dict:
    """Parse a Markdown file.

    :param filepath: The path and filename of the Markdown file to be parsed.
    :return: A dictionary containing the metadata and content of the Markdown file.
    """
    data = Path(filepath).read_text(encoding='utf-8')
    md = markdown.Markdown(
        extensions=[
            'meta',
            TocExtension(title='Contents', permalink=True, toc_depth=2),
            CodeHiliteExtension(guess_lang=False),
        ],
        output_format='html5',
    )

    return {
        'html': md.convert(data),
        'metadata': md.Meta,
    }


def get_page_vars(filepath: str) -> Dict:
    """Extract variables from a Markdown file, such as the metadata fields and the
    content of the file.

    :param filepath: The path and filename of the Markdown file to be processed.
    :return: A dictionary containing the page variables.
    """
    data = parse_markdown(filepath)
    template_vars = {'content': data['html']}

    for field, value in data['metadata'].items():
        if field == 'date_published':
            template_vars[field] = datetime.strptime(value[0], '%d %b %Y')
        else:
            template_vars[field] = value[0] if len(value) == 1 else value

    return template_vars


def build_tag_page(page_category: str, tag: str, pages: List[Dict]):
    """Create an HTML page that lists items with a given tag.

    :param page_category: The type of page, such as 'blog' or 'project'.
    :param tag: The tag name.
    :param pages: A list of pages that have the given tag. Each page is a
     dictionary of page variables, extracted from the page's corresponding
     Markdown file.
    """
    # Items on a page, such as blog posts or projects, are listed from most to
    # least recent.
    items = sorted(pages, key=lambda x: x['date_published'], reverse=True)

    template = env.get_template(f'{page_category}.html')
    write_file(
        f'{page_category}/tag/{tag}',
        template.render(category=page_category, tag=tag, items=items),
    )


def build_detail_pages(parent_page, detail_pages: List[Dict]):
    for detail_page in detail_pages:
        template = env.get_template(f'{parent_page.detail_page_template}.html')
        write_file(
            f"{parent_page.category}/{detail_page['slug']}",
            template.render(category=parent_page.category, page=detail_page),
        )


def build_list_page(page: Page) -> Tuple[List[Dict], Dict]:
    """Create an HTML page that lists items, such as blog posts or projects.

    :param page: The page to be created.
    :return:
    """
    items = []
    tags: Dict[str, List] = defaultdict(list)
    source_dir = str(page.source_dir)

    for f in os.listdir(source_dir):
        filepath = join(source_dir, f)

        if not isfile(filepath):
            continue

        page_vars = get_page_vars(filepath)

        if 'title' in page_vars:
            page_vars['slug'] = slugify(page_vars['title'])

        items.append(page_vars)

        if 'tags' in page_vars:
            for tag in page_vars['tags']:
                tags[tag].append(page_vars)

    # Items on a page, such as blog posts or projects, are listed from most to
    # least recent.
    items = sorted(items, key=lambda x: x['date_published'], reverse=True)

    template = env.get_template(f'{page.template}.html')
    write_file(page.category, template.render(category=page.category, items=items))

    return items, tags


def build_simple_page(page: Page):
    """Create an HTML page from a template.

    :param page_name: The name of the page to build, excluding the extension.
    """
    template = env.get_template(f'{page.template}.html')
    write_file(page.category, template.render(category=page.category))


if __name__ == "__main__":
    env = Environment(
        autoescape=True,
        loader=FileSystemLoader(searchpath=TEMPLATES_PATH),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Ensure some build directories exist
    Path(f'{BUILD_PATH}/blog/tag/').mkdir(parents=True, exist_ok=True)

    # A place to keep track of all tags
    all_tags: Dict[Tuple[str, str], List] = defaultdict(list)

    # Build each top level page
    for page in PAGES:
        if page.listing:
            items, tags = build_list_page(page)

            if page.create_detail_pages:
                build_detail_pages(page, items)

            for tag, page_vars in tags.items():
                all_tags[(page.category, tag)].extend(page_vars)
        else:
            build_simple_page(page)

    # Build the tag pages
    for (page_category, tag), page_vars in all_tags.items():
        build_tag_page(page_category, tag, page_vars)

    # Copy the static files to the build directory
    copytree(STATIC_ASSETS_PATH, BUILD_PATH, dirs_exist_ok=True)
