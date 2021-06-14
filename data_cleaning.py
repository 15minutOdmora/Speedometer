import csv
import glob
from datetime import datetime
import os


def read_data(path: str, extension: str = ".csv"):
    """
    Function reads all data from path, can be single file or directory.
    :param path: str -> Path of file or directory.
    :param extension: str -> extension type of files to read, preset to .csv files.
    :return: list, list(list(), list(),...) -> list containing headers, list containing all data rows as lists.
    """
    paths = []
    # Check if given path is valid.
    if not os.path.exists(path):
        raise ValueError("Given path does not exists: {}".format(path))
    if os.path.isfile(path):
        # If its file, check extension and save to paths
        if path.endswith(extension):
            paths.append(path)
        else:
            print("No files with given extension {}".format(extension))
    elif os.path.isdir(path):
        # If its dir. traverse through all files
        for file_path in glob.glob(os.path.join(path, "*{}".format(extension))):
            paths.append(file_path)
        if not paths:
            print("No files with given extension {}".format(extension))

    # Traverse through all files only saving the first header
    header = []
    data_list = []
    for file_path in paths:
        with open(file_path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            ct = 1
            for row in reader:
                if not header or ct == 1:  # If header hasn't been set, not perfect but hey it does the job
                    header = row
                else:  # Transform data to correct data types
                    t_row = list(map(lambda x: float(x), row))
                    data_list += [t_row]
                ct += 1

    return header, data_list


def clean_data(header, data_list, out_file="cleaned_data.csv", **kwargs):
    """
    Function cleas data, removes rows which don't fit the parameters set in kwargs
    :param header: list -> Header row for csv output file
    :param data_list: list(list(), list(), ...) -> List containing data rows
    :param out_file: str -> Path containing output file for saving cleaned data
    :param kwargs: Kwargs consist of multiple parameters:
        - utc= int -> Utc of timezone. ex. +2 for Slovenia, setting utc affects all other datetime based parameters
        - between_hours= (int, int) -> Interval of hours of the day to accept data, preset to (0, 24), if utc was set, this should be set with utc in mind
        - max_speed= float -> Maximum speed the object has traveled
        - min_time_diff= float -> Minimum time difference between two consecutive objects
        - max_size= float -> Maximum size of object
        - min_size= float -> Minimum size of object
        - exclude_datetime= list(tuple(from, to), ...) List consisting of multiple tuple pairs (from, to) where
                            from and to are str in the format of a date 'dd-mm-yy hh:mm:ss', data between these
                            points will be ignored.
    :return:
    """
    # Determine arguments
    keys = kwargs.keys()
    if "utc" in keys:
        utc = kwargs["utc"]  # UTC time based on timezone slovenia = +2 so utc=2
        utc_sec = utc * 3600
    else:
        utc = 0
        utc_sec = 0
    if "max_speed" in keys:  # This is set in kmh
        max_speed = kwargs["max_speed"]
    else:
        max_speed = float("inf")
    if "min_time_diff" in keys:  # Between two consedutive objects
        min_time_diff = kwargs["min_time_diff"]
    else:
        min_time_diff = 0
    if "max_size" in keys:
        max_size = kwargs["max_size"]
    else:
        max_size = float("inf")
    if "min_size" in keys:
        min_size = kwargs["min_size"]
    else:
        min_size = 0
    if "between_hours" in keys:
        between_hours = kwargs["between_hours"]  # tuple/list containing the range of hours of day
    else:
        between_hours = (0, 24)
    if "exclude_datetime" in keys:
        # This is a list containing tuple of pairs consisting od two times (from, to) from which to exclude data
        # date times should be set in the format dd-mm-yyyy hh:mm:ss
        exclude_datetime = []
        to_exclude = kwargs["exclude_datetime"]
        for from_, to_ in to_exclude:
            unix_from = datetime.strptime(from_, "%d-%m-%y %H:%M:%S").timestamp()
            unix_to = datetime.strptime(to_, "%d-%m-%y %H:%M:%S").timestamp()
            exclude_datetime.append((unix_from, unix_to))
    else:
        exclude_datetime = []

    def detrmine_number_type(x: any):
        """
        Function tries to convert string into int or float, if not possible returns a string
        :param x: str -> to be converted
        :return: int, float or string
        """
        try:
            return float(x)
        except ValueError:
            return x

    def check_row(row, prev_row=None):
        """
        Function checks if row fits the given parameters.
        :param row: list(col1, col2, ...) list containing data from each row
        :param prev_row: list(col1, col2, ...) list containing data form previous row
        :return: bool -> True if row fits the parameters
        """
        # id,start_time,end_time,time_diff,x_dir,y_dir,start_frame,end_frame,frame_diff,calculated_time,speed_mps,speed_kmh,avg_size
        speed = row[-2]
        end_time = row[2] + utc_sec# This is always in unix
        size = row[-1]
        if prev_row is not None:
            prev_end_time = prev_row[2] + utc_sec
        else:
            prev_end_time = 0

        if max_speed < speed:
            return False
        if abs(end_time - prev_end_time) < min_time_diff:
            return False
        if max_size < size or size < min_size:
            return False
        # Check if timed is between hours
        h = int(datetime.utcfromtimestamp(end_time).strftime("%H"))
        if not(between_hours[0] <= h < between_hours[1]):
            return False
        for from_time, to_time in exclude_datetime:
            if from_time + utc_sec < end_time < to_time + utc_sec:
                return False
        return True

    # Append new row to header -> datetime, which are strings representing date time
    header.append("datetime")
    # Clean data and write to file
    cleaned_data_counter = 0
    rejected_data = []
    with open(out_file, 'w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(header)
        prev_row = None
        for row in data_list:
            # Check if it fits the parameters
            if check_row(row, prev_row):
                # Write to out_file
                new_row = list(map(detrmine_number_type, row))
                # Save additional row representing datetime
                new_row.append(datetime.utcfromtimestamp(new_row[1] + utc_sec))
                writer.writerow(new_row)  # Write to file
                cleaned_data_counter += 1
            else:
                rejected_data.append(row)
            prev_row = row

    total_rows = len(rejected_data) + cleaned_data_counter
    # Print data regarding cleaning
    resoult_str = "{} rows read, {} were rejected {} were accepted. \n{}% of all rows were rejected.".format(total_rows,
                                                                                                             len(rejected_data),
                                                                                                             cleaned_data_counter,
                                                                                               round(len(rejected_data)/total_rows, 4) * 100)
    print(resoult_str)
    return rejected_data


if __name__ == "__main__":
    header, data = read_data(r"C:\Users\Liam\PycharmProjects\Speedometer\Data")
    # dd-mm-yyyy hh:mm:ss
    ignore = [
        ("18-05-21 21:00:00", "19-05-21 21:00:00"),
        ("16-05-21 22:36:00", "17-05-21 18:33:00")
    ]
    rej_data = clean_data(header, data, max_speed=100, max_size=15000, min_size=2500, min_time_diff=0.6, between_hours=(6, 21), utc=2, exclude_datetime=ignore)
