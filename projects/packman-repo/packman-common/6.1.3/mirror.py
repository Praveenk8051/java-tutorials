import os
import sys
import logging

import packman
import utils
import schemaparser
import errors


logger = logging.getLogger("packman")


def mirror(project_file_path, target_remote, platform_names=None, auto_yes=False):
    """
    :param str project_file_path: path to project file to process
    :param str target_remote: name of remote to mirror to
    :param sequence platform_names: sequence of platform names to match against the spec in 'project_file_path'
    :param bool auto_yes: whether to automatically answer all interactive questions with a yes,
        making them non-interactive.
    """
    if not os.path.exists(project_file_path):
        raise errors.PackmanError("Project file path '%s' does not exist!" % project_file_path)
    if not platform_names:
        with open(project_file_path, "r") as input_file:
            input_data = input_file.read()
            if "${platform}" in input_data:
                raise errors.PackmanError(
                    "Project file '%s' uses ${platform} template but no platform argument provided!"
                    % project_file_path
                )
    project = packman.parse_project_file(project_file_path)
    target_remote_config = packman.get_remote_config_with_parsed_project(target_remote, project)
    source_remote_names, source_remote_configs = packman.get_remote_names_and_configs_with_parsed_project(
        None, project
    )

    if platform_names:
        for platform in platform_names:
            deps = project.get_dependencies(platform)
            if deps:
                mirror_dependencies(
                    target_remote_config, source_remote_names, source_remote_configs, auto_yes, deps
                )
            else:
                logger.warning("No dependencies to process for platform '%s'", platform)
    else:
        deps = project.get_dependencies(None)
        if deps:
            mirror_dependencies(
                target_remote_config, source_remote_names, source_remote_configs, auto_yes, deps
            )
        else:
            logger.warning("No dependencies to process - do you need to provide platform argument?")


def mirror_dependencies(
    target_remote_config, source_remote_names, source_remote_configs, auto_yes, dependencies
):
    # process labels into packages
    packman.process_labels_in_dependencies(dependencies, source_remote_names, source_remote_configs)
    tp = {}  # we delay creation of transport until it's actually needed
    package_repo_dir = None  # we delay look up of this until it's actually needed
    dependencies_processed = []
    target_remote_name = target_remote_config.name
    with utils.TemporaryDirectory() as temp_dir:
        for dep in list(dependencies.values()):
            dep_name = dep.name
            env_base_name = dep_name
            if dep_name not in dependencies_processed:
                dependencies_processed.append(dep_name)
                child = dep.children[0]
                if isinstance(child, schemaparser.Source):
                    logger.info(
                        "Dependency '%s' is fulfilled by source at '%s'", dep_name, child.path
                    )
                else:
                    package_name = child.name
                    package_version = child.version
                    # check to see if we need to create transport
                    if target_remote_name not in tp:
                        tp[target_remote_name] = packman.create_transport(target_remote_config)
                    # see if package exists on remote
                    package_path = tp[target_remote_name].get_package_path(
                        package_name, package_version
                    )
                    if not package_path:
                        # package is missing from target - need to copy it over:
                        print(
                            "Package name '%s' at version '%s' is missing from target remote"
                            % (package_name, package_version)
                        )
                        if not auto_yes:
                            res = input(
                                "Do you want to copy package to remote '%s' [Y/n]: "
                                % target_remote_name
                            )
                            if res.startswith("n"):
                                continue
                        print("Mirroring ...")
                        if child.remotes:
                            package_remotes = child.remotes[:]
                            package_remotes.extend(source_remote_names)
                        else:
                            package_remotes = source_remote_names
                        if not package_remotes:
                            raise errors.PackmanError(
                                "No remote configured for package '%s' at version '%s'"
                                % (package_name, package_version)
                            )
                        for remote_name in package_remotes:
                            if remote_name not in tp:
                                remote_config = packman.get_remote_config_from_name(
                                    remote_name, source_remote_configs
                                )
                                tp[remote_name] = packman.create_transport(remote_config)
                            # see if package exists on remote
                            source_package_path = tp[remote_name].get_package_path(
                                package_name, package_version
                            )
                            if not source_package_path:
                                continue  # package doesn't exist on this server
                            package_found = True
                            head, package_filename = os.path.split(source_package_path)
                            target_filename = os.path.join(temp_dir, package_filename)
                            tp[remote_name].download_file(source_package_path, target_filename)
                            tp[target_remote_name].upload_file(target_filename, package_filename)
                            break
                        if not source_package_path:
                            raise errors.PackmanError(
                                "Package not found on specified remote servers!"
                            )


if __name__ == "__main__":
    import packmanapi

    path = r"C:\Users\hfannar.NVIDIA.COM\target-deps.packman.xml"
    mirror(path, "mygtl", platform_names=["windows-x86_64", "linux-x86_64"], auto_yes=True)
