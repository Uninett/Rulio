from datetime import datetime
import logging
import os


def write_configuration_to_file(
    config,
    filepath,
    file_dir,
    vendor,
    logger_name,
    generated_by="tests",
    log_for_vendors=None,
):
    if log_for_vendors is None:
        log_for_vendors = ["juniper"]

    os.makedirs(file_dir, exist_ok=True)

    # Make directory writable by everyone so files can be removed more easily
    try:
        os.chmod(file_dir, 0o777)
    except OSError:
        pass

    logger = logging.getLogger(logger_name)
    filepath = str(filepath).split(".")[0]  # Remove file extension if present

    if hasattr(config, "items"):
        config_items = list(config.items())
    else:
        config_items = [(filepath, config)]

    multiple_files = len(config_items) > 1

    for i, (filename, content) in enumerate(config_items, start=1):
        indexed_filename = f"{filepath}_{i:02d}.yaml" if multiple_files else f"{filepath}.yaml"

        if vendor in log_for_vendors:
            logger.info(
                "\n=== Generated config: %s ===\n%s\n=== End config ===",
                indexed_filename,
                content,
            )

        with open(indexed_filename, "w") as f:
            f.write(f"# Generated on {datetime.now()}\n")
            f.write(f"# Test for generating from {generated_by}\n\n")
            f.write(content)

        # Make file fully writable/readable so cleanup is easier
        try:
            os.chmod(indexed_filename, 0o666)
        except OSError:
            pass
