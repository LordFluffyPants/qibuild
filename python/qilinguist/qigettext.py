## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Library to extract, generate, update and compile translatable sentences with gettext"""

import os
from qisys import ui
import qisys
import qisys.command

def generate_pot_file(text_domain, input_files, output_file,
                      input_dir=None, output_dir=None):
    """generate POT. Extract gettext strings from source files

    :param text_domain: Use for output
    :param input_file:  List of input file
    :param output_file: Write output to specified file
    :param input_dir:   Add directories to list for input files search
    :param output_dir:  Output file will be placed here

    """
    cmd = ["xgettext", "--default-domain=" + text_domain]
    cmd.append("--keyword=_")

    # generate sorted output
    cmd.append("--sort-output")

    # output files will be placed here
    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    # write output to specified file
    cmd.extend(["--output", output_file])

    # add directories to list for input files search
    if input_dir:
        cmd.extend(["--directory", input_dir])

    #  List of input file
    if input_files:
        cmd.extend(input_files)

    qisys.command.call(cmd)

def generate_po_file(input_file, output_file, locale, output_dir=None):
    """generate PO file for locale

    :param input_file:  Input POT file
    :param output_file: Write output to specified PO file
    :param locale:      Set target locales
    :param output_dir:  Output file will be placed here

    """
    # init
    cmd = ["msginit", "--no-translator"]
    # set target locale
    cmd.extend(["--locale", locale])

    out = output_dir if output_dir else ""

    out = os.path.join(out, output_file)
    # write output to specified PO file
    cmd.extend(["--output-file", out])

    # input POT file
    cmd.extend(["--input", input_file])

    ui.info(ui.green, "Creating", ui.reset, ui.bold, out)
    qisys.command.call(cmd, quiet=True)

def generate_mo_file(input_file, output_file, input_dir=None, output_dir=None):
    """generate MO file

    :param input_file:  Input PO file
    :param output_file: Write output to specified file
    :param input_dir:   Add directories to list for input files search
    :param output_dir:  Output file will be placed here

    """
    # check PO file
    cmd = ["msgfmt", "--check", "--statistics"]

    out = os.path.join(output_dir, output_file) if output_dir else output_file

    to_make = os.path.dirname(out)
    qisys.sh.mkdir(to_make, recursive=True)

    # write output to specified MO file
    cmd.extend(["--output-file", out])

    if input_dir:
        cmd.extend(["--directory", input_dir])

    # Input PO file
    cmd.append(input_file)

    ui.info(ui.green, "Generating", ui.reset, ui.bold, out)
    qisys.command.call(cmd)

def update_po_file(input_file, update_file, input_dir=None, update_dir=None):
    """update PO file from new POT

    :param input_file:  Input POT file
    :param update_file: Write output to specified file
    :param input_dir:   Add directories to list for input files search
    :param update_dir:  Output file will be placed here

    """
    # init command sorted update_file
    # update update (do nothing if update_file already up to date)
    cmd = ["msgmerge", "--sort-output", "--update"]

    if input_dir:
        cmd.extend(["--directory", input_dir])

    update = os.path.join(update_dir, update_file) if update_dir else update_file

    # write update to specified MO file
    cmd.append(update)

    # Input PO file
    cmd.append(input_file)

    ui.info(ui.green, "Updating", ui.reset, ui.bold, update)
    qisys.command.call(cmd, quiet=True)
