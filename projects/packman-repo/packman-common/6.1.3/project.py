import xml.etree.ElementTree as ET
import os
import logging
import xml.dom.minidom
from typing import Iterable

import schemaparser


logger = logging.getLogger("packman.project")


def create_project(project_file_path: str, force_overwrite: bool = False):
    if os.path.exists(project_file_path) and not force_overwrite:
        raise RuntimeError(
            "Project file '%s' exists! Use force option to overwrite." % project_file_path
        )
    attribs = {schemaparser.ProjectElement.TOOLSVERSION: schemaparser.SUPPORTED_TOOLSVERSION}
    project_element = ET.Element(schemaparser.ProjectElement.TAG, attribs)
    _write_element_to_file(project_element, project_file_path)


def _write_element_to_file(element, project_file_path):
    tree = ET.ElementTree(element)
    tree.write(project_file_path, encoding="utf8")


def _get_project_element_from_file(project_file_path):
    # make sure the file exists:
    if not os.path.exists(project_file_path):
        raise RuntimeError("Project file '%s' does not exist!" % project_file_path)
    tree = ET.parse(project_file_path)
    project_element = tree.getroot()
    tag = schemaparser.ProjectElement.TAG
    if project_element.tag != tag:
        raise RuntimeError("Project file is malformed. Missing %s element at root." % tag)
    # update to current version of packman (if newer) to avoid any mishaps due to new elements/attributes
    # supported by a newer version of packman:
    toolsversion = schemaparser.ProjectElement.TOOLSVERSION
    project_file_version = project_element.attrib[toolsversion]
    if not schemaparser.ProjectElement.is_file_version_newer(
        project_file_version, schemaparser.SUPPORTED_TOOLSVERSION
    ):
        project_element.attrib[toolsversion] = schemaparser.SUPPORTED_TOOLSVERSION
    return project_element


def _get_dependency_element(project_element, dependency_name):
    for dep in project_element.iter(schemaparser.DependencyElement.TAG):
        if dep.attrib["name"] == dependency_name:
            return dep
    return None


def add_dependency(
    project_file_path: str,
    dep_name: str,
    link_path: str = None,
    tags: Iterable[str] = None,
    force_overwrite: bool = False,
):
    project_element = _get_project_element_from_file(project_file_path)
    dep = _get_dependency_element(project_element, dep_name)
    if dep is not None:
        if force_overwrite:
            project_element.remove(dep)
        else:
            raise RuntimeError("Dependency already exists. Use force option to overwrite.")

    # We have optimized the dependency modification - now let's see if we can add the dependency in the proper places:
    attribs = {schemaparser.DependencyElement.NAME: dep_name}
    if link_path:
        attribs[schemaparser.DependencyElement.LINKPATH] = link_path
    if tags:
        attribs[schemaparser.DependencyElement.TAGS] = " ".join(tags)

    ET.SubElement(project_element, schemaparser.DependencyElement.TAG, attribs)

    _write_element_to_file(project_element, project_file_path)


def remove_dependency(project_file: str, dep_name: str):
    project_element = _get_project_element_from_file(project_file)
    dep = _get_dependency_element(project_element, dep_name)
    if dep is not None:
        project_element.remove(dep)
        _write_element_to_file(project_element, project_file)


def add_package(
    project_file_path: str,
    dep_name: str,
    package_name: str,
    package_version: str,
    platforms: Iterable[str] = None,
    force_overwrite: bool = False,
):
    project_element = _get_project_element_from_file(project_file_path)
    dep = _get_dependency_element(project_element, dep_name)
    if dep is None:
        raise RuntimeError("Dependency '%s' not found!" % dep_name)
    package_element = None
    for package in dep.iter(schemaparser.PackageElement.TAG):
        if schemaparser.PackageElement.PLATFORMS in package.attrib:
            if platforms:
                package_platforms = package.attrib[schemaparser.PackageElement.PLATFORMS].split()
                if set(package_platforms) == set(platforms):
                    package_element = package
        else:
            package_element = package

    if package_element is not None:
        if force_overwrite:
            dep.remove(package_element)
        else:
            if platforms:
                platform_str = " for specified platforms"
            else:
                platform_str = ""
            msg = "Package named '%s' already exists%s! Use force option to overwrite." % (
                package_name,
                platform_str,
            )
            raise RuntimeError(msg)

    attributes = {
        schemaparser.PackageElement.NAME: package_name,
        schemaparser.PackageElement.VERSION: package_version,
    }
    if platforms:
        attributes[schemaparser.PackageElement.PLATFORMS] = " ".join(platforms)
    ET.SubElement(dep, schemaparser.PackageElement.TAG, attributes)
    _write_element_to_file(project_element, project_file_path)


def main():
    logging.basicConfig(level=logging.INFO)
    proj = "test.xml"
    create_project(proj, force_overwrite=True)
    add_dependency(proj, "A", link_path="blarg")
    add_dependency(proj, "B", tags=["all", "bingo"])
    add_package(proj, "B", "package", "version", ["win.vs2013", "win.vs2015"])
    add_package(proj, "B", "package", "version")


if __name__ == "__main__":
    main()
