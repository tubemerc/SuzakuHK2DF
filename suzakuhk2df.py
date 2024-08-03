import os

import astropy.io.fits
import pandas as pd
import yaml


class SuzakuHK2DF:
    def __init__(self, start_datetime: str, end_datetime: str, data_dir_path: str):
        self.start_datetime = pd.to_datetime(start_datetime)
        self.end_datetime = pd.to_datetime(end_datetime)
        self.data_dir_path = data_dir_path

    def setup(self, output_data_filter: bool = False):
        cd = os.path.dirname(os.path.abspath(__file__))
        # Setup filename_list
        table = pd.read_csv(os.path.join(cd, "conf/suzaku_data_list.csv"))
        table["observation_start_time"] = pd.to_datetime(
            table["observation_start_time"]
        )
        table["observation_end_time"] = pd.to_datetime(table["observation_end_time"])
        start_idx = table[table["observation_start_time"] <= self.start_datetime].index[
            -1
        ]
        end_idx = table[table["observation_end_time"] >= self.end_datetime].index[0]
        self.filename_list = (
            table[start_idx : end_idx + 1]["data_access_url"]
            .apply(self._url2filename)
            .to_list()
        )
        # Setup data_filter
        with open(os.path.join(cd, "conf/filters.yaml")) as f:
            conf = yaml.safe_load(f)
            excluded_unit_list = conf["exclude_unit_filter"]
            exclude_unit_filter = bool(excluded_unit_list)
            included_data_name_list = conf["data_name_filter"]
            include_name_filter = bool(included_data_name_list)
            calibration_filter = conf["calibration_filter"]
        with astropy.io.fits.open(
            "%s/%s" % (self.data_dir_path, self.filename_list[0])
        ) as f:
            self.data_filter = pd.DataFrame(columns=["index", "data_name", "unit"])
            for i, hdu in enumerate(f):
                for header, value in hdu.header.items():
                    if "UNIT" in header:
                        if exclude_unit_filter and value in excluded_unit_list:
                            continue
                        name = hdu.header.get(header.replace("TUNIT", "TTYPE"))
                        if include_name_filter and not any(
                            label in name for label in included_data_name_list
                        ):
                            continue
                        if calibration_filter and name[-4:] != "_CAL":
                            continue
                        self.data_filter = pd.concat(
                            [
                                self.data_filter,
                                pd.DataFrame(
                                    [[i, name, value]],
                                    columns=self.data_filter.columns,
                                ),
                            ],
                            ignore_index=True,
                            axis=0,
                        )
        if output_data_filter:
            return self.data_filter

    def _url2filename(self, url):
        return "ae%s.hk" % url.rstrip("/").split("/")[-1]

    def hk2df(
        self,
        fill_nan: bool = False,
        resample_interval_sec: int = None,
        variance_threshold: float = None,
    ):
        df = pd.DataFrame()
        total_index = len(set(self.data_filter["index"].values))
        for i in set(self.data_filter["index"].values):
            print("Processing index: %d/%d" % (i, total_index))
            data_name_list = self.data_filter[self.data_filter["index"] == i][
                "data_name"
            ].to_list()
            for j, filename in enumerate(self.filename_list):
                with astropy.io.fits.open(
                    "%s/%s" % (self.data_dir_path, filename)
                ) as f:
                    data = f[i].data
                    datetime = [
                        pd.to_datetime(x + y, format="%Y%m%d%H%M%S")
                        for (x, y) in zip(
                            [str(x) for x in data.field("YYYYMMDD")],
                            [str(x).zfill(6) for x in data.field("HHMMSS")],
                        )
                    ]
                    df_per_file = pd.DataFrame(index=datetime, columns=data_name_list)
                    for data_name in data_name_list:
                        df_per_file[data_name] = data.field(data_name)
                    if j == 0:
                        df_per_index = df_per_file.copy()
                    else:
                        df_per_index = pd.concat(
                            [df_per_index, df_per_file.copy()], axis=0
                        )
            df_per_index.sort_index(inplace=True)
            df_per_index = df_per_index[~df_per_index.index.duplicated(keep="first")]
            if resample_interval_sec is not None:
                df_per_index = self._resampling(df_per_index, resample_interval_sec)
            df = pd.merge(
                df, df_per_index.copy(), how="outer", left_index=True, right_index=True
            )
        df.sort_index(inplace=True)
        if resample_interval_sec is not None:
            df = self._resampling(df, resample_interval_sec)
        if fill_nan:
            df.ffill(inplace=True)
        df = df.loc[self.start_datetime : self.end_datetime]
        if variance_threshold is not None:
            df = df.loc[:, df.var() > variance_threshold]
        return df

    def _resampling(self, df, interval_sec):
        return df.resample(
            str(interval_sec) + "s",
            label="right",
            closed="right",
        ).median()
