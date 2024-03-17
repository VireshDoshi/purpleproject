import glob
from datetime import date


def get_todays_date() -> str:
    return f'{date.today():%Y/%m/%d}'


def get_latest_properties_folder() -> str:
    items = glob.iglob('./purpleline/data/properties/202[0-9]/[0-9][0-9]/[0-9][0-9]',  # noqa: E501
                       recursive=True)

    latest_folders = sorted(items, reverse=True)
    split_latest_folder = latest_folders[0].split("/")
    latest_folder = split_latest_folder[-3:]
    return latest_folder[0] + '/' + latest_folder[1] + '/' + latest_folder[2]


def get_latest_properties_folder_list() -> list:
    items = glob.iglob('./purpleline/data/properties/202[0-9]/[0-9][0-9]/[0-9][0-9]',  # noqa: E501
                       recursive=True)
    folderlist = []
    reverse_folders_full = sorted(items, reverse=True)
    for folder in reverse_folders_full:
        split_latest_folder = folder.split("/")
        latest_folder = split_latest_folder[-3:]
        folderlist.append(latest_folder[0] + '/' + latest_folder[1] + '/' + latest_folder[2])
    return folderlist
