##
# pycor/dispatcher.py
#   dispatch function(s)
#
#   This file is a part of the pycor project. To obtain the latest
#   development version, head over to the git repository available
#   at github: https://github.com/Jayfrown/pycor
#
#   Copyright (C) 2018  Jeroen de Boer (info@jayfrown.nl)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from .loghandler import logger
from .pylxdclient import lxd, lxdException
from . import overlay

def launch(containerName):
    """
    create an empty container, mount overlayfs and start it
    create base container if it does not exist

    :param containerName: the new container's name
    :return: the pylxd container object
    """

    # create base container if it does not exist
    try:
        lxd.containers.get('base')
    except lxdException.NotFound:
        logger.debug("initializing base environment")
        overlay.create_base()

    # create empty container
    logger.debug("creating {}".format(containerName))
    container = overlay.create(containerName)

    # mount overlayfs
    logger.debug("mounting overlayfs")
    overlay.mount(container.name)

    # start container
    container.start(wait=True)
    logger.debug("{} state {}".format(container.name, container.status))
    logger.info("created {}".format(container.name))
    return container

# dispatch based on cli args
def dispatch(cmd, args):

    # launch a new container
    if cmd == "launch":

        if args:
            containerName = args[0]
        else:
            import requests
            link = "https://frightanic.com/goodies_content/docker-names.php"
            logger.debug("fetching docker-like name")
            containerName = requests.get(link).text.strip().replace("_", "-")

        # new container on overlayfs
        try:
            launch(containerName)
        except Exception as e:
            import sys
            logger.debug("launch: caught exception")
            traceback = sys.exc_info()[2]

            try:
                container = lxd.containers.get(containerName)
                logger.debug("launch: handling exception: deleting {}".format(container.name))
                container.delete()
                logger.debug("launch: raising exception")
                raise Exception, e, traceback
            except NameError:
                raise Exception, e, traceback


    # umount overlay and delete container
    elif cmd == "delete":

        if args:
            container = lxd.containers.get(args[0])
        else:
            raise RuntimeError("delete: which one?")

        # refuse to delete running container
        if container.status == "Running":
            logger.debug("{} state {}".format(container.name, container.status))
            raise RuntimeError("{} is running, refusing to delete".format(container.name))

        logger.info("note: umount not yet implemented")
        container.delete(wait=True)
        logger.info("deleted {}".format(container.name))

    # catch-all
    else:
        raise RuntimeError("{}: unknown action".format(cmd))
