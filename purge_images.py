# @Author: flbla
# @Date:   2018-08-17T09:45:19+02:00
# @Filename: purge_images.py
# @Last modified by:   florian
# @Last modified time: 2018-08-17T10:06:05+02:00

#!/usr/bin/python3

import os
import errno
import ast
import json
import shutil
from time import gmtime, strftime
import logging
import logging.handlers
import argparse

def copytree(src, dst):
    if os.path.isdir(src):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for name in os.listdir(src):
            copytree(os.path.join(src, name),
                     os.path.join(dst, name))
    else:
        shutil.copyfile(src, dst)

def mkdir(directory):
	try:
	    os.makedirs(directory)
	except OSError as e:
	    if e.errno != errno.EEXIST:
	        raise

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''Purge Docker Registry V1;''')
    parser.add_argument('-p', metavar='registry', nargs=1, help='registry path', required=True)
    parser.add_argument('-b', metavar='backup', nargs=1, help='backup path', required=True)
    args = parser.parse_args()
    REGISTRY_PATH = (vars(args))['p'][0]
    DELETE_PATH = (vars(args))['b'][0]

    count = 0
    images = [f for f in os.listdir(REGISTRY_PATH + "/images")]
    used_images = []
    unused_images = []
    ancestries = []
    LOG_FILENAME = '/var/log/purge_docker_registry.log'
    needRoll = os.path.isfile(LOG_FILENAME)

    logger = logging.getLogger('purge_images')
    hdlr = logging.FileHandler(LOG_FILENAME)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME, backupCount=10)
    hdlr.doRollover()
    logger.addHandler(hdlr)
    hdlr.setFormatter(formatter)
    logger.setLevel(logging.INFO)

    logger.info('Start purge')
    shutil.rmtree(DELETE_PATH, ignore_errors=True)
    mkdir(DELETE_PATH + "/images")
    mkdir(DELETE_PATH + "/repositories")

    # Backup repositories
    mkdir(DELETE_PATH + "/repositories/")
    copytree(REGISTRY_PATH + "/repositories/", DELETE_PATH + "/repositories/")

    logger.info('Registry has been backuped')

    # Find all images directly exposed
    for path, sub_dir, files in os.walk(REGISTRY_PATH + "/repositories"):
    	if len(files) > 0:
    		for file in files:
    			if "tag_" in file:
    				with open(path + "/" + file, 'r') as content_file:
    					content = content_file.read()
    					used_images.append(content)

    logger.info('Actual number of images : ' + str(len(used_images)))

    # Find all ancestries
    for image in used_images:
    	with open(REGISTRY_PATH + "/images/" + image + "/ancestry", 'r') as content_file:
    		content = content_file.read()
    		for ancestry in ast.literal_eval(content):
    			ancestries.append(ancestry)
    uniq_ancestries = set(ancestries)
    logger.info('Actual number of ancestries : ' + str(len(uniq_ancestries)))

    # Move images that are not exposed neither ancestry to DELETE_PATH/images/
    for image in images:
    	if image not in used_images:
    		if image not in uniq_ancestries:
    			unused_images.append(image)
    			shutil.move(REGISTRY_PATH + "/images/" + image, DELETE_PATH + "/images/" + image)

    logger.info('Actual number of unused images : ' + str(len(unused_images)))
    logger.info('All unused images has been moved to : ' + DELETE_PATH + "/images/")

    # Rewrite index files
    for path, sub_dir, files in os.walk(REGISTRY_PATH + "/repositories"):
    	if len(files) > 0:
    		for file in files:
    			if "_index_images" in file:
    				new_content = []
    				with open(path + "/" + file, 'r') as content_file:
    					content = json.load(content_file)
    					for line in content:
    						if line['id'] not in unused_images:
    							new_content.append(line)
    				with open(path + "/" + file, 'w') as outfile:
    					json.dump(new_content, outfile)
    logger.info('End purge')

if __name__ == '__main__':
    main()
