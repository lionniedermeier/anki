# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Builds the browse sidebar tree as a plain protobuf structure, for the
Svelte Browse page. Mirrors the section builders in
aqt.browser.sidebar.tree.SidebarTreeView, but omits interaction-only concerns
(Qt models, drag-and-drop, context menus, rename/delete, expand-state
persistence) which stay native for now.
"""

from __future__ import annotations

from collections.abc import Iterable

import aqt
from anki.collection import Collection, Config, SearchNode
from anki.decks import DeckTreeNode
from anki.frontend_pb2 import BrowseSidebarNode
from anki.tags import TagTreeNode
from aqt.utils import tr

NodeType = BrowseSidebarNode.NodeType


def build_browse_sidebar(mw: aqt.AnkiQt) -> BrowseSidebarNode:
    col = mw.col
    root = BrowseSidebarNode(name="", node_type=NodeType.ROOT)

    _saved_searches(col, root)
    _today(col, root)
    _flags(mw, root)
    _card_state(col, root)
    _decks(col, root)
    _notetypes(col, root)
    _tags(col, root)

    return root


def _search(col: Collection, node: SearchNode | None) -> str:
    if node is None:
        return ""
    return col.build_search_string(node)


def _section_root(
    col: Collection,
    root: BrowseSidebarNode,
    name: str,
    node_type: BrowseSidebarNode.NodeType.V,
    collapse_key: Config.Bool.V,
    search_node: SearchNode | None = None,
) -> BrowseSidebarNode:
    section = root.children.add()
    section.name = name
    section.node_type = node_type
    section.expanded = not col.get_config_bool(collapse_key)
    section.search = _search(col, search_node)
    return section


def _saved_searches(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_saved_searches(),
        NodeType.SAVED_SEARCH_ROOT,
        Config.Bool.COLLAPSE_SAVED_SEARCHES,
    )
    saved = col.get_config("savedFilters", {})
    for name, filt in sorted(saved.items()):
        child = section.children.add()
        child.name = name
        child.node_type = NodeType.SAVED_SEARCH
        child.search = filt


def _today(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col, root, tr.browsing_today(), NodeType.TODAY_ROOT, Config.Bool.COLLAPSE_TODAY
    )

    def add(name: str, node: SearchNode) -> None:
        child = section.children.add()
        child.name = name
        child.node_type = NodeType.TODAY
        child.search = _search(col, node)

    add(tr.browsing_sidebar_due_today(), SearchNode(due_on_day=0))
    add(tr.browsing_added_today(), SearchNode(added_in_days=1))
    add(tr.browsing_edited_today(), SearchNode(edited_in_days=1))
    add(tr.browsing_studied_today(), SearchNode(rated=SearchNode.Rated(days=1)))
    add(tr.browsing_sidebar_first_review(), SearchNode(introduced_in_days=1))
    add(
        tr.browsing_sidebar_rescheduled(),
        SearchNode(
            rated=SearchNode.Rated(days=1, rating=SearchNode.RATING_BY_RESCHEDULE)
        ),
    )
    add(
        tr.browsing_again_today(),
        SearchNode(rated=SearchNode.Rated(days=1, rating=SearchNode.RATING_AGAIN)),
    )
    add(
        tr.browsing_sidebar_overdue(),
        col.group_searches(
            SearchNode(card_state=SearchNode.CARD_STATE_DUE),
            SearchNode(negated=SearchNode(due_on_day=0)),
        ),
    )


def _card_state(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_card_state(),
        NodeType.CARD_STATE_ROOT,
        Config.Bool.COLLAPSE_CARD_STATE,
    )

    def add(name: str, state: SearchNode.CardState.V) -> None:
        child = section.children.add()
        child.name = name
        child.node_type = NodeType.CARD_STATE
        child.search = _search(col, SearchNode(card_state=state))

    add(tr.actions_new(), SearchNode.CARD_STATE_NEW)
    add(tr.scheduling_learning(), SearchNode.CARD_STATE_LEARN)
    add(tr.browsing_sidebar_card_state_review(), SearchNode.CARD_STATE_REVIEW)
    add(tr.browsing_suspended(), SearchNode.CARD_STATE_SUSPENDED)
    add(tr.browsing_buried(), SearchNode.CARD_STATE_BURIED)


def _flags(mw: aqt.AnkiQt, root: BrowseSidebarNode) -> None:
    col = mw.col
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_flags(),
        NodeType.FLAG_ROOT,
        Config.Bool.COLLAPSE_FLAGS,
        search_node=SearchNode(flag=SearchNode.FLAG_ANY),
    )

    none_child = section.children.add()
    none_child.name = tr.browsing_no_flag()
    none_child.node_type = NodeType.FLAG_NONE
    none_child.search = _search(col, SearchNode(flag=SearchNode.FLAG_NONE))

    for flag in mw.flags.all():
        child = section.children.add()
        child.name = flag.label
        child.node_type = NodeType.FLAG
        child.id = flag.index
        child.search = _search(col, flag.search_node)


def _decks(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_decks(),
        NodeType.DECK_ROOT,
        Config.Bool.COLLAPSE_DECKS,
        search_node=SearchNode(deck="_*"),
    )

    current = section.children.add()
    current.name = tr.browsing_current_deck()
    current.node_type = NodeType.DECK_CURRENT
    current.id = col.decks.selected()
    current.search = _search(col, SearchNode(deck="current"))

    def render(
        parent: BrowseSidebarNode, nodes: Iterable[DeckTreeNode], head: str
    ) -> None:
        for node in nodes:
            child = parent.children.add()
            child.name = node.name
            child.node_type = NodeType.DECK
            child.id = node.deck_id
            child.expanded = not node.collapsed
            child.search = _search(col, SearchNode(deck=head + node.name))
            render(child, node.children, f"{head + node.name}::")

    render(section, col.decks.deck_tree().children, "")


def _notetypes(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_notetypes(),
        NodeType.NOTETYPE_ROOT,
        Config.Bool.COLLAPSE_NOTETYPES,
        search_node=SearchNode(note="_*"),
    )

    for nt in sorted(col.models.all(), key=lambda nt: nt["name"].lower()):
        item = section.children.add()
        item.name = nt["name"]
        item.node_type = NodeType.NOTETYPE
        item.id = nt["id"]
        item.search = _search(col, SearchNode(note=nt["name"]))

        for c, tmpl in enumerate(nt["tmpls"]):
            child = item.children.add()
            child.name = tmpl["name"]
            child.node_type = NodeType.NOTETYPE_TEMPLATE
            child.id = tmpl["ord"]
            child.search = _search(
                col,
                col.group_searches(SearchNode(note=nt["name"]), SearchNode(template=c)),
            )

        for c, fld in enumerate(nt["flds"]):
            child = item.children.add()
            child.name = fld["name"]
            child.node_type = NodeType.NOTETYPE_FIELD
            child.id = fld["ord"]
            child.search = _search(
                col,
                col.group_searches(
                    SearchNode(note=nt["name"]), SearchNode(field_name=fld["name"])
                ),
            )


def _tags(col: Collection, root: BrowseSidebarNode) -> None:
    section = _section_root(
        col,
        root,
        tr.browsing_sidebar_tags(),
        NodeType.TAG_ROOT,
        Config.Bool.COLLAPSE_TAGS,
        search_node=SearchNode(tag="_*"),
    )

    untagged = section.children.add()
    untagged.name = tr.browsing_sidebar_untagged()
    untagged.node_type = NodeType.TAG_NONE
    untagged.search = _search(col, SearchNode(negated=SearchNode(tag="_*")))

    def render(
        parent: BrowseSidebarNode, nodes: Iterable[TagTreeNode], head: str
    ) -> None:
        for node in nodes:
            child = parent.children.add()
            child.name = node.name
            child.node_type = NodeType.TAG
            child.expanded = not node.collapsed
            child.search = _search(col, SearchNode(tag=head + node.name))
            render(child, node.children, f"{head + node.name}::")

    render(section, col.tags.tree().children, "")
