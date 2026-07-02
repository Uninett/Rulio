from datetime import datetime
import logging
import os


def write_configuration_to_file(
    config, filepath, file_dir, vendor, logger_name, generated_by="tests", log_for_vendors=None
):
    if log_for_vendors is None:
        log_for_vendors = ["juniper"]

    os.makedirs(file_dir, exist_ok=True)

    i = 0
    filepath = str(filepath).split(".")[0]  # Remove file extension if present
    for filename, content in config.items():
        i += 1
        indexed_filename = f"{filepath}_{i:02d}.yaml" if len(config.items()) > 1 else f"{filepath}.yaml"
        if vendor in log_for_vendors:
            logger = logging.getLogger(logger_name)
            logger.info(
                "\n=== Generated config: %s ===\n%s\n=== End config ===",
                indexed_filename,
                content,
            )

        with open(indexed_filename, "w") as f:
            f.write(f"# Generated on {datetime.now()}\n# Test for generating from {generated_by} \n\n")
            f.write(content)
