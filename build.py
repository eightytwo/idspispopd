from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import copytree
from shutil import rmtree
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import markdown
from jinja2 import Environment
from jinja2 import FileSystemLoader
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.toc import TocExtension
from slugify import slugify


@dataclass(frozen=True)
class Page:
    category: str
    template: str
    listing: bool = False
    create_detail_pages: bool = False
    detail_page_template: Optional[str] = None
    source_dir: Optional[Path] = None


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
        source_dir=Path('content/blog'),
    ),
    Page(
        category='projects',
        template='projects',
        listing=True,
        source_dir=Path('content/projects'),
    ),
]


def write_file(name: Path, content: str, suffix: str = ".html"):
    """Write an HTML file to disk.

    :param name: The path and name of the file, excluding extension.
    :param content: The content of the file.
    :param suffix: The extension of the file.
    """
    file = BUILD_PATH / name.with_suffix(suffix)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8", errors="xmlcharrefreplace")


def parse_markdown(filepath: Path) -> Dict:
    """Parse a Markdown file.

    :param filepath: The path and filename of the Markdown file to be parsed.
    :return: A dictionary containing the metadata and content of the Markdown file.
    """
    data = filepath.read_text(encoding='utf-8')
    md = markdown.Markdown(
        extensions=[
            'meta',
            TocExtension(title='Contents', permalink=True, toc_depth=2),
            CodeHiliteExtension(guess_lang=False),
            FootnoteExtension(),
        ],
        output_format='html5',
    )

    return {
        'html': md.convert(data),
        'metadata': md.Meta,
    }


def get_page_vars(filepath: Path) -> Dict:
    """Extract variables from a Markdown file, such as the metadata fields and the
    content of the file.

    :param filepath: The path and filename of the Markdown file to be processed.
    :return: A dictionary containing the page variables.
    """
    data = parse_markdown(filepath)
    template_vars = {'content': data['html']}

    for field, value in data['metadata'].items():
        if field.startswith('date_'):
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
        Path(page_category, "tag", tag),
        template.render(category=page_category, tag=tag, items=items),
    )


def build_detail_pages(parent_page, detail_pages: List[Dict]):
    """Create an HTML page for each item that appears in a parent list page.

    :param parent_page: The page that displays a list of items.
    :param detail_pages: The data for the list items that will have pages
     created for them.
    """
    for detail_page in detail_pages:
        output_dir = Path(parent_page.category, detail_page['slug'])
        output_file = output_dir / 'index'
        template = env.get_template(f'{parent_page.detail_page_template}.html')
        write_file(
            output_file,
            template.render(category=parent_page.category, page=detail_page),
        )

        # Check if this detail page (e.g. a blog post page or project page) has any
        # assets, such as images or videos. If so, copy these assets to the build
        # directory.
        assets_dir = parent_page.source_dir / detail_page['filename'].stem
        if assets_dir.is_dir():
            copytree(assets_dir, Path(BUILD_PATH, output_dir), dirs_exist_ok=True)


def build_list_page(page: Page) -> Tuple[List[Dict], Dict]:
    """Create an HTML page that lists items, such as blog posts or projects.

    Items that appear on the list page are gathered into a list so individual
    pages can be created. While processing these items, a map of tags is also
    built.

    :param page: The list page to be created.
    :return: The items that appear in the list along with a map of tags.
    """
    items = []
    tags: Dict[str, List] = defaultdict(list)

    if page.source_dir:
        for file in page.source_dir.iterdir():
            if not file.is_file():
                continue

            page_vars = get_page_vars(file)
            page_vars['filename'] = file

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
    write_file(
        Path(page.category), template.render(category=page.category, items=items)
    )

    return items, tags


def build_simple_page(page: Page):
    """Create an HTML page from a template.

    :param page: The page to build.
    """
    template = env.get_template(f'{page.template}.html')
    write_file(Path(page.category), template.render(category=page.category))


if __name__ == "__main__":
    env = Environment(
        loader=FileSystemLoader(searchpath=TEMPLATES_PATH),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Clean the build directory
    if Path(BUILD_PATH).exists():
        rmtree(BUILD_PATH)

    # Ensure some build directories exist
    Path(f'{BUILD_PATH}/blog/tag/').mkdir(parents=True, exist_ok=True)

    # Copy the static files to the build directory
    copytree(STATIC_ASSETS_PATH, BUILD_PATH, dirs_exist_ok=True)

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
