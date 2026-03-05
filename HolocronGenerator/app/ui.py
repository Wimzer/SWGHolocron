from __future__ import annotations

from typing import Dict, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from .model import HolocronProject, HolocronCategory, PageNode, PageLink, PageImage, is_valid_short_name
from .project_io import load_project, save_project
from .swg_loader import load_project_from_swg
from .generator import generate_project
from .link_tools import find_path, validate_link_target, sanitize_key
from .tree_ops import move_node_down, move_node_up


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Holocron Generator")

        self.project = HolocronProject()
        self.project_path: str = ""
        self.is_dirty: bool = False
        self.current_category: Optional[HolocronCategory] = None
        self.current_node: Optional[PageNode] = None
        self.node_item_map: Dict[PageNode, QTreeWidgetItem] = {}
        self.item_node_map: Dict[QTreeWidgetItem, PageNode] = {}
        self.drafts: Dict[PageNode, Tuple[str, str, str]] = {}

        self._build_ui()
        self._new_project()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        path_group = QGroupBox("SWG Root / Output")
        path_layout = QHBoxLayout(path_group)
        self.swg_root_edit = QLineEdit()
        self.swg_root_button = QPushButton("Browse")
        self.swg_root_button.clicked.connect(self._browse_swg_root)
        path_layout.addWidget(QLabel("SWG Root"))
        path_layout.addWidget(self.swg_root_edit)
        path_layout.addWidget(self.swg_root_button)

        project_buttons = QHBoxLayout()
        self.load_project_button = QPushButton("Load Project")
        self.save_project_button = QPushButton("Save Project")
        self.load_swg_button = QPushButton("Load from SWG")
        self.generate_button = QPushButton("Generate Output")

        self.load_project_button.clicked.connect(self._load_project)
        self.save_project_button.clicked.connect(self._save_project)
        self.load_swg_button.clicked.connect(self._load_from_swg)
        self.generate_button.clicked.connect(self._generate_output)

        project_buttons.addWidget(self.load_project_button)
        project_buttons.addWidget(self.save_project_button)
        project_buttons.addWidget(self.load_swg_button)
        project_buttons.addWidget(self.generate_button)

        category_group = QGroupBox("Categories")
        category_layout = QHBoxLayout(category_group)
        self.category_combo = QComboBox()
        self.category_add_button = QPushButton("Add")
        self.category_remove_button = QPushButton("Remove")
        self.category_rename_button = QPushButton("Rename")
        self.category_switch_button = QPushButton("Switch To")
        self.category_add_button.clicked.connect(self._add_category)
        self.category_remove_button.clicked.connect(self._remove_category)
        self.category_rename_button.clicked.connect(self._rename_category)
        self.category_switch_button.clicked.connect(self._switch_to_selected_category)

        category_layout.addWidget(QLabel("Category"))
        category_layout.addWidget(self.category_combo)
        category_layout.addWidget(self.category_add_button)
        category_layout.addWidget(self.category_remove_button)
        category_layout.addWidget(self.category_rename_button)
        category_layout.addWidget(self.category_switch_button)

        splitter = QSplitter()

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._on_tree_selection_changed)
        left_layout.addWidget(self.tree)

        tree_buttons = QHBoxLayout()
        self.add_page_button = QPushButton("Add Page")
        self.add_subpage_button = QPushButton("Add Subpage")
        self.delete_page_button = QPushButton("Delete")
        self.move_up_button = QPushButton("Move Up")
        self.move_down_button = QPushButton("Move Down")

        self.add_page_button.clicked.connect(self._add_page)
        self.add_subpage_button.clicked.connect(self._add_subpage)
        self.delete_page_button.clicked.connect(self._delete_page)
        self.move_up_button.clicked.connect(self._move_up)
        self.move_down_button.clicked.connect(self._move_down)

        tree_buttons.addWidget(self.add_page_button)
        tree_buttons.addWidget(self.add_subpage_button)
        tree_buttons.addWidget(self.delete_page_button)
        tree_buttons.addWidget(self.move_up_button)
        tree_buttons.addWidget(self.move_down_button)
        left_layout.addLayout(tree_buttons)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        editor_group = QGroupBox("Page Editor")
        editor_layout = QVBoxLayout(editor_group)

        self.short_name_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.content_edit = QPlainTextEdit()

        editor_layout.addWidget(QLabel("Short Name"))
        editor_layout.addWidget(self.short_name_edit)
        editor_layout.addWidget(QLabel("Page Title"))
        editor_layout.addWidget(self.title_edit)
        editor_layout.addWidget(QLabel("Page Content"))
        editor_layout.addWidget(self.content_edit)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_current_node)
        editor_layout.addWidget(self.apply_button)

        images_group = QGroupBox("Images")
        images_layout = QVBoxLayout(images_group)
        self.image_list = QListWidget()
        self.image_list.currentItemChanged.connect(self._on_image_selected)
        images_layout.addWidget(self.image_list)

        self.image_name_edit = QLineEdit()
        self.image_resource_edit = QLineEdit()

        images_layout.addWidget(QLabel("Image Name"))
        images_layout.addWidget(self.image_name_edit)
        images_layout.addWidget(QLabel("Resource (/texture/*.dds)"))
        images_layout.addWidget(self.image_resource_edit)

        image_buttons = QHBoxLayout()
        self.image_add_button = QPushButton("Add Image")
        self.image_update_button = QPushButton("Update")
        self.image_remove_button = QPushButton("Remove")

        self.image_add_button.clicked.connect(self._add_image)
        self.image_update_button.clicked.connect(self._update_image)
        self.image_remove_button.clicked.connect(self._remove_image)

        image_buttons.addWidget(self.image_add_button)
        image_buttons.addWidget(self.image_update_button)
        image_buttons.addWidget(self.image_remove_button)
        images_layout.addLayout(image_buttons)

        links_group = QGroupBox("Links")
        links_layout = QVBoxLayout(links_group)
        self.link_list = QListWidget()
        self.link_list.currentItemChanged.connect(self._on_link_selected)
        links_layout.addWidget(self.link_list)

        self.link_label_edit = QLineEdit()
        self.link_target_edit = QLineEdit()
        self.link_key_edit = QLineEdit()

        links_layout.addWidget(QLabel("Link Label"))
        links_layout.addWidget(self.link_label_edit)
        links_layout.addWidget(QLabel("Target Path"))
        links_layout.addWidget(self.link_target_edit)
        links_layout.addWidget(QLabel("Key (optional)"))
        links_layout.addWidget(self.link_key_edit)

        link_buttons = QHBoxLayout()
        self.link_add_button = QPushButton("Add Link")
        self.link_update_button = QPushButton("Update")
        self.link_remove_button = QPushButton("Remove")
        self.link_jump_button = QPushButton("Jump")

        self.link_add_button.clicked.connect(self._add_link)
        self.link_update_button.clicked.connect(self._update_link)
        self.link_remove_button.clicked.connect(self._remove_link)
        self.link_jump_button.clicked.connect(self._jump_to_link)

        link_buttons.addWidget(self.link_add_button)
        link_buttons.addWidget(self.link_update_button)
        link_buttons.addWidget(self.link_remove_button)
        link_buttons.addWidget(self.link_jump_button)
        links_layout.addLayout(link_buttons)

        right_layout.addWidget(editor_group, 3)
        right_layout.addWidget(images_group, 1)
        right_layout.addWidget(links_group, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        root_layout.addWidget(path_group)
        root_layout.addLayout(project_buttons)
        root_layout.addWidget(category_group)
        root_layout.addWidget(splitter)

        self.setCentralWidget(root)
        self._build_menus()

    def _build_menus(self) -> None:
        menu = self.menuBar()
        menu.clear()

        file_menu = menu.addMenu("File")
        help_menu = menu.addMenu("Help")

        load_action = file_menu.addAction("Load Project...")
        save_action = file_menu.addAction("Save")
        save_as_action = file_menu.addAction("Save As...")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")

        load_action.setShortcut("Ctrl+O")
        save_action.setShortcut("Ctrl+S")
        save_as_action.setShortcut("Ctrl+Shift+S")
        exit_action.setShortcut("Alt+F4")

        load_action.triggered.connect(self._load_project)
        save_action.triggered.connect(self._save_project)
        save_as_action.triggered.connect(self._save_project_as)
        exit_action.triggered.connect(self.close)

        help_action = help_menu.addAction("Help Guide")
        credits_action = help_menu.addAction("Credits")
        help_action.triggered.connect(self._show_help)
        credits_action.triggered.connect(self._show_credits)

    def _new_project(self) -> None:
        self.project = HolocronProject()
        default = HolocronCategory(name="custom")
        self.project.add_category(default)
        self.project_path = ""
        self.is_dirty = False
        self._refresh_category_combo(default.name)
        self._switch_to_category(default.name)

    def _browse_swg_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select SWG Root")
        if path:
            self.swg_root_edit.setText(path)

    def _refresh_category_combo(self, select_name: str | None = None) -> None:
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        for name in self.project.category_names():
            self.category_combo.addItem(name)
        self.category_combo.blockSignals(False)
        if select_name:
            idx = self.category_combo.findText(select_name)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

    def _switch_to_selected_category(self) -> None:
        name = self.category_combo.currentText()
        if not name:
            return
        self._switch_to_category(name)

    def _switch_to_category(self, name: str) -> None:
        self._store_current_draft()
        category = self.project.get_category(name)
        if category is None:
            return
        self.current_category = category
        self.current_node = None
        self._rebuild_tree()
        self._clear_editor()

    def _rebuild_tree(self) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        self.node_item_map.clear()
        self.item_node_map.clear()
        if not self.current_category:
            self.tree.blockSignals(False)
            return
        for root in self.current_category.root_pages:
            item = self._build_tree_item(root)
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        self.tree.blockSignals(False)

    def _build_tree_item(self, node: PageNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.short_name])
        self.node_item_map[node] = item
        self.item_node_map[item] = node
        for child in node.children:
            item.addChild(self._build_tree_item(child))
        return item

    def _on_tree_selection_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem) -> None:
        if previous is not None:
            prev_node = self.item_node_map.get(previous)
            if prev_node:
                self._store_draft(prev_node)
        self.current_node = self.item_node_map.get(current) if current else None
        self._load_current_node()

    def _store_current_draft(self) -> None:
        if self.current_node:
            self._store_draft(self.current_node)

    def _store_draft(self, node: PageNode) -> None:
        self.drafts[node] = (
            self.short_name_edit.text(),
            self.title_edit.text(),
            self.content_edit.toPlainText(),
        )

    def _load_current_node(self) -> None:
        if not self.current_node:
            self._clear_editor()
            return
        if self.current_node in self.drafts:
            short_name, title, content = self.drafts[self.current_node]
        else:
            short_name = self.current_node.short_name
            title = self.current_node.title
            content = self.current_node.content
        self.short_name_edit.setText(short_name)
        self.title_edit.setText(title)
        self.content_edit.setPlainText(content)
        self._refresh_images()
        self._refresh_links()

    def _clear_editor(self) -> None:
        self.short_name_edit.clear()
        self.title_edit.clear()
        self.content_edit.clear()
        self.image_list.clear()
        self.image_name_edit.clear()
        self.image_resource_edit.clear()
        self.link_list.clear()
        self.link_label_edit.clear()
        self.link_target_edit.clear()
        self.link_key_edit.clear()

    def _apply_current_node(self) -> None:
        if not self.current_node or not self.current_category:
            return
        short_name = self.short_name_edit.text().strip()
        if not is_valid_short_name(short_name):
            QMessageBox.warning(self, "Invalid Short Name", "Short name must start with a letter and contain only letters, numbers, or underscores.")
            return
        if self._path_conflicts(self.current_node, short_name):
            QMessageBox.warning(self, "Duplicate Path", "Another page already uses this full path.")
            return

        self.current_node.short_name = short_name
        self.current_node.title = self.title_edit.text()
        self.current_node.content = self.content_edit.toPlainText()
        self.drafts.pop(self.current_node, None)
        self.is_dirty = True

        item = self.node_item_map.get(self.current_node)
        if item:
            item.setText(0, self.current_node.short_name)
        self._refresh_links()

    def _path_conflicts(self, node: PageNode, new_short_name: str) -> bool:
        if not self.current_category:
            return False
        parent = node.parent
        if parent is None:
            new_path = new_short_name
        else:
            new_path = f"{parent.full_path()}.{new_short_name}"
        for other in self.current_category.walk():
            if other is node:
                continue
            if other.full_path() == new_path:
                return True
        return False

    def _add_page(self) -> None:
        if not self.current_category:
            return
        new_name = self._unique_short_name("new_page")
        node = PageNode(short_name=new_name, title="", content="")
        self.current_category.add_root(node)
        self.is_dirty = True
        self._rebuild_tree()
        self._select_node(node)

    def _add_subpage(self) -> None:
        if not self.current_category or not self.current_node:
            return
        new_name = self._unique_short_name("new_page", parent=self.current_node)
        node = PageNode(short_name=new_name, title="", content="")
        self.current_node.add_child(node)
        self.is_dirty = True
        self._rebuild_tree()
        self._select_node(node)

    def _unique_short_name(self, base: str, parent: Optional[PageNode] = None) -> str:
        candidate = base
        counter = 1
        while True:
            if parent is None:
                path = candidate
            else:
                path = f"{parent.full_path()}.{candidate}"
            if not self.current_category:
                return candidate
            if not self.current_category.find_by_path(path):
                return candidate
            counter += 1
            candidate = f"{base}{counter}"

    def _delete_page(self) -> None:
        if not self.current_category or not self.current_node:
            return
        reply = QMessageBox.question(self, "Delete Page", "Delete the selected page and its children?")
        if reply != QMessageBox.Yes:
            return
        parent = self.current_node.parent
        if parent is None:
            self.current_category.remove_root(self.current_node)
        else:
            parent.remove_child(self.current_node)
        self.current_node = None
        self.is_dirty = True
        self._rebuild_tree()
        self._clear_editor()

    def _move_up(self) -> None:
        if not self.current_category or not self.current_node:
            return
        if move_node_up(self.current_category, self.current_node):
            self.is_dirty = True
            self._rebuild_tree()
            self._select_node(self.current_node)

    def _move_down(self) -> None:
        if not self.current_category or not self.current_node:
            return
        if move_node_down(self.current_category, self.current_node):
            self.is_dirty = True
            self._rebuild_tree()
            self._select_node(self.current_node)

    def _select_node(self, node: PageNode) -> None:
        item = self.node_item_map.get(node)
        if item:
            self.tree.setCurrentItem(item)

    def _is_valid_image_resource(self, resource: str) -> bool:
        value = (resource or "").strip()
        if not value:
            return False
        lower = value.lower()
        return lower.startswith("/texture/") and lower.endswith(".dds")

    def _refresh_images(self) -> None:
        self.image_list.clear()
        if not self.current_node:
            return
        for image in self.current_node.images:
            text = f"{image.name or '(unnamed)'} -> {image.resource}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, image)
            if not self._is_valid_image_resource(image.resource):
                item.setForeground(Qt.red)
                item.setText(f"{text} (invalid)")
            self.image_list.addItem(item)

    def _on_image_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        image = current.data(Qt.UserRole) if current else None
        if not image:
            self.image_name_edit.clear()
            self.image_resource_edit.clear()
            return
        self.image_name_edit.setText(image.name)
        self.image_resource_edit.setText(image.resource)

    def _add_image(self) -> None:
        if not self.current_node:
            return
        name = self.image_name_edit.text().strip()
        resource = self.image_resource_edit.text().strip()
        if not resource:
            QMessageBox.warning(self, "Missing Fields", "Image resource is required.")
            return
        if not self._is_valid_image_resource(resource):
            QMessageBox.warning(self, "Invalid Resource", "Image resource must be /texture/<name>.dds")
            return
        image = PageImage(resource=resource, name=name)
        self.current_node.add_image(image)
        self.is_dirty = True
        self._refresh_images()

    def _update_image(self) -> None:
        if not self.current_node:
            return
        item = self.image_list.currentItem()
        if not item:
            return
        image = item.data(Qt.UserRole)
        if not image:
            return
        name = self.image_name_edit.text().strip()
        resource = self.image_resource_edit.text().strip()
        if not resource:
            QMessageBox.warning(self, "Missing Fields", "Image resource is required.")
            return
        if not self._is_valid_image_resource(resource):
            QMessageBox.warning(self, "Invalid Resource", "Image resource must be /texture/<name>.dds")
            return
        image.name = name
        image.resource = resource
        self.is_dirty = True
        self._refresh_images()

    def _remove_image(self) -> None:
        if not self.current_node:
            return
        item = self.image_list.currentItem()
        if not item:
            return
        image = item.data(Qt.UserRole)
        if not image:
            return
        self.current_node.remove_image(image)
        self.is_dirty = True
        self._refresh_images()

    def _refresh_links(self) -> None:
        self.link_list.clear()
        if not self.current_node:
            return
        for link in self.current_node.links:
            text = f"{link.label} -> {link.target}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, link)
            if not validate_link_target(self.project, link.target):
                item.setForeground(Qt.red)
                item.setText(f"{text} (missing)")
            self.link_list.addItem(item)

    def _on_link_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        link = current.data(Qt.UserRole) if current else None
        if not link:
            self.link_label_edit.clear()
            self.link_target_edit.clear()
            self.link_key_edit.clear()
            return
        self.link_label_edit.setText(link.label)
        self.link_target_edit.setText(link.target)
        self.link_key_edit.setText(link.key)

    def _add_link(self) -> None:
        if not self.current_node:
            return
        label = self.link_label_edit.text().strip()
        target = self.link_target_edit.text().strip()
        key = self.link_key_edit.text().strip()
        if not label or not target:
            QMessageBox.warning(self, "Missing Fields", "Link label and target are required.")
            return
        if not validate_link_target(self.project, target):
            QMessageBox.warning(self, "Invalid Target", "Target path does not exist in the project.")
            return
        link = PageLink(label=label, target=target, key=key)
        self.current_node.add_link(link)
        self.is_dirty = True
        self._refresh_links()

    def _update_link(self) -> None:
        if not self.current_node:
            return
        item = self.link_list.currentItem()
        if not item:
            return
        link = item.data(Qt.UserRole)
        if not link:
            return
        label = self.link_label_edit.text().strip()
        target = self.link_target_edit.text().strip()
        key = self.link_key_edit.text().strip() or sanitize_key(label)
        if not label or not target:
            QMessageBox.warning(self, "Missing Fields", "Link label and target are required.")
            return
        if not validate_link_target(self.project, target):
            QMessageBox.warning(self, "Invalid Target", "Target path does not exist in the project.")
            return
        link.label = label
        link.target = target
        link.key = key
        link.label_token = ""
        self.is_dirty = True
        self._refresh_links()

    def _remove_link(self) -> None:
        if not self.current_node:
            return
        item = self.link_list.currentItem()
        if not item:
            return
        link = item.data(Qt.UserRole)
        if not link:
            return
        self.current_node.remove_link(link)
        self.is_dirty = True
        self._refresh_links()

    def _jump_to_link(self) -> None:
        item = self.link_list.currentItem()
        if not item:
            return
        link = item.data(Qt.UserRole)
        if not link:
            return
        match = find_path(self.project, link.target, self.current_category)
        if not match:
            QMessageBox.warning(self, "Not Found", "Target path does not exist.")
            return
        category, node = match
        self._refresh_category_combo(category.name)
        self._switch_to_category(category.name)
        self._select_node(node)

    def _load_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            project = load_project(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", str(e))
            return
        self.project = project
        self.project_path = path
        self.is_dirty = False
        names = self.project.category_names()
        if not names:
            self._new_project()
            return
        self._refresh_category_combo(names[0])
        self._switch_to_category(names[0])

    def _save_project(self) -> None:
        if not self.project_path:
            path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
            if not path:
                return
            self.project_path = path
        try:
            save_project(self.project_path, self.project)
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))
            return
        self.is_dirty = False
        QMessageBox.information(self, "Saved", f"Project saved to {self.project_path}")

    def _save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "JSON Files (*.json)")
        if not path:
            return
        self.project_path = path
        self._save_project()

    def _load_from_swg(self) -> None:
        root = self.swg_root_edit.text().strip()
        if not root:
            QMessageBox.warning(self, "Missing Path", "Select the SWG root path first.")
            return
        try:
            project = load_project_from_swg(root)
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", str(e))
            return
        self.project = project
        self.project_path = ""
        self.is_dirty = True
        names = self.project.category_names()
        if not names:
            self._new_project()
            return
        self._refresh_category_combo(names[0])
        self._switch_to_category(names[0])

    def _generate_output(self) -> None:
        root = self.swg_root_edit.text().strip()
        if not root:
            QMessageBox.warning(self, "Missing Path", "Select the SWG root path first.")
            return
        try:
            generate_project(self.project, root, language="en")
        except Exception as e:
            QMessageBox.critical(self, "Generate Failed", str(e))
            return
        QMessageBox.information(self, "Generated", "Datatables and STF files generated successfully.")

    def _show_help(self) -> None:
        text = (
            "Holocron Generator Help\n\n"
            "File Menu:\n"
            "- Load Project: open a saved JSON project.\n"
            "- Save / Save As: write the project JSON.\n\n"
            "Workflow:\n"
            "1) Select a category and click 'Switch To'.\n"
            "2) Add pages/subpages, edit fields, then click Apply.\n"
            "3) Add links and use Jump to navigate.\n"
            "4) Add images with resource /texture/<name>.dds.\n"
            "5) Use Load from SWG to import existing KB data.\n"
            "6) Generate Output to write SWG files.\n\n"
            "Output Paths:\n"
            "- datatables/knowledgebase/<category>.iff\n"
            "- datatables/knowledgebase/filelist.iff\n"
            "- string/<lang>/kb/kb_<category>_n.stf\n"
            "- string/<lang>/kb/kb_<category>_d.stf\n\n"
            "Notes:\n"
            "- Image resources MUST be /texture/<name>.dds."
        )
        QMessageBox.information(self, "Help", text)

    def _show_credits(self) -> None:
        text = (
            "Holocron Generator\n"
            "Created for Wimzer\n"
            "Built with PySide6\n"
            "Licensed under GPL-3.0"
        )
        QMessageBox.information(self, "Credits", text)

    def _add_category(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok:
            return
        name = name.strip().lower()
        if not name:
            return
        if self.project.get_category(name):
            QMessageBox.warning(self, "Duplicate", "Category name already exists.")
            return
        category = HolocronCategory(name=name)
        self.project.add_category(category)
        self.is_dirty = True
        self._refresh_category_combo(name)

    def _remove_category(self) -> None:
        name = self.category_combo.currentText()
        if not name:
            return
        category = self.project.get_category(name)
        if not category:
            return
        reply = QMessageBox.question(self, "Remove Category", f"Remove category '{name}'?")
        if reply != QMessageBox.Yes:
            return
        self.project.remove_category(category)
        self.is_dirty = True
        names = self.project.category_names()
        if not names:
            self._new_project()
            return
        self._refresh_category_combo(names[0])
        self._switch_to_category(names[0])

    def _rename_category(self) -> None:
        current = self.category_combo.currentText()
        if not current:
            return
        category = self.project.get_category(current)
        if not category:
            return
        name, ok = QInputDialog.getText(self, "Rename Category", "New name:", text=current)
        if not ok:
            return
        name = name.strip().lower()
        if not name:
            return
        if name != current and self.project.get_category(name):
            QMessageBox.warning(self, "Duplicate", "Category name already exists.")
            return
        category.name = name
        self.is_dirty = True
        self._refresh_category_combo(name)
        self._switch_to_category(name)

    def closeEvent(self, event) -> None:
        if not self.is_dirty:
            event.accept()
            return
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save before exiting?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if reply == QMessageBox.Save:
            self._save_project()
            if self.is_dirty:
                event.ignore()
                return
            event.accept()
            return
        if reply == QMessageBox.Cancel:
            event.ignore()
            return
        event.accept()
