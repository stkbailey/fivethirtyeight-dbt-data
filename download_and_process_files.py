import logging
import pandas
import pathlib
import shutil
import subprocess
import yaml

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel("INFO")

fivethirtyeight_readme = """See https://data.fivethirtyeight.com/ for a list of the data and code we've published.\n
Unless otherwise noted, our data sets are available under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/),
and the code is available under the [MIT License](https://opensource.org/licenses/MIT).
If you find this information useful, please [let us know](mailto:data@fivethirtyeight.com)."""

class FiveThirtyEightDataParser:
    
    _git_repo = "https://github.com/fivethirtyeight/data.git"

    def __init__(self, max_file_size=100000):
        self.directory = pathlib.Path().cwd()

        if not (self.directory / "data").exists():
            logger.info("Cloning data from FiveThirtyEight...")
            self.clone_git_repo()
            logger.info("Removing projects with too-large files or no CSVs...")
            self.prune_incompatible_projects(max_file_size)
            self.files = self.build_csv_df()
            self.rewrite_all_files()
        else:
            logger.info("'data' directory found. Skipping project prune and renaming.")
            self.files = self.build_csv_df()

        for project in self.files["project_path"].unique().tolist():
            self.process_data_dir(project)

    def clone_git_repo(self):
        "Clones the 538 Git Repo. Should be run from top-level of DBT repo"
        subprocess.run(["git", "clone", self._git_repo])

    def build_csv_df(self):
        all_csvs = [self.parse_csv_path(p) for p in self.directory.glob("data/*/*.csv")]
        df = pandas.DataFrame(all_csvs)
        return df

    def parse_csv_path(self, p):
      def rename_file_by_project(csv_name, project_name):
          if csv_name.replace("-", "_").startswith(project_name.replace("-", "_")):
              new_name = f"{csv_name}.csv".lower().replace("-", "_").replace(" ", "_")
          else:
              new_name = f"{project_name}_{csv_name}.csv".lower().replace("-", "_").replace(" ", "_")
          return new_name
      
      return {
        "file_name_orig": p.stem,
        "file_path": p,
        "project": p.parent.name,
        "project_path": p.parent,
        "file_size": p.stat().st_size,
        "file_name_new": rename_file_by_project(p.stem, p.parent.name)
      }

    def prune_incompatible_projects(self, max_file_size_bytes):
        for p in self.directory.glob("data/*"):
            if not p.is_dir():
                p.unlink()
            else:
                project_files = list(p.glob("*"))
                csvs = list(filter(lambda x: x.suffix == ".csv", project_files))
                readmes = list(filter(lambda x: x.name.lower() == "readme.md", project_files))
                if not csvs or not readmes:
                    logging.info("Removing %s: Either CSVs or README is missing.", p.name)
                    shutil.rmtree(p)
                elif any(csv.stat().st_size > max_file_size_bytes for csv in csvs):
                    logging.info("Removing %s: A CSV is too large.", p.name)
                    shutil.rmtree(p)
                else:
                    shutil.move(p, p.parent / p.name.replace("-","_"))


    def rewrite_all_files(self):
        def rewrite_file(s):
            new_path = s["project_path"] / s["file_name_new"]
            tdf = pandas.read_csv(
                s["file_path"], 
                dtype="string", 
                lineterminator='\n', 
                encoding="ISO-8859-1"
            )
            tdf.to_csv(new_path, encoding="utf-8", index=None)

        for ii, s in self.files.iterrows():
            logger.info("Rewriting %s to %s...", s["file_path"].name, s["file_name_new"])
            rewrite_file(s)
            logger.info("\tUnlinking file.")
            s["file_path"].unlink()

        self.files = self.build_csv_df()

    def convert_readme_to_schema(self, readme_path, csv_paths):
        txt = readme_path.read_text()
        txt_pad = txt.replace("\n", "\n    ")
        footer_pad = fivethirtyeight_readme.replace('\n', '\n    ')
        schema = "version: 2\n\nseeds:\n"
        for csv in csv_paths:
            data_source_name = csv.stem
            schema += f"- name: {data_source_name}\n  description: |\n    {txt_pad}\n"
        schema += f"    ---\n    {footer_pad}"
        return schema

    def write_schema_file(self, data_dir, schema_text):
        d = data_dir / "schema.yml"
        d.write_text(schema_text)

    def parse_data_dir(self, data_dir):
        files = list(data_dir.glob("*"))
        readme_path = list(filter(lambda x: "readme" in x.name.lower(),  files))[0]
        csv_paths = list(filter(lambda x: ".csv" == x.suffix,  files))
        return readme_path, csv_paths

    def clean_up_data_dir(self, data_dir):
        files = list(data_dir.glob("*"))
        rm_files = filter(lambda p: p.suffix not in (".yml", ".csv"), files)
        if data_dir / "schema.yml" in files:
            for f in rm_files:
                try:
                    f.unlink()
                except PermissionError:
                    shutil.rmtree(f)

    def process_data_dir(self, data_dir):
        readme, csvs = self.parse_data_dir(data_dir)
        schema_text = self.convert_readme_to_schema(readme, csvs)
        self.write_schema_file(data_dir, schema_text)
        self.clean_up_data_dir(data_dir)

if __name__ == "__main__":
    parser = FiveThirtyEightDataParser()




# def build_index_df(directory):
#     df = pandas.read_csv(directory / "index.csv").fillna(False)
#     df["in_data_dir"] = df["dataset_url"].str.contains("/data/tree/master")
#     df["project_dir"] = df["dataset_url"].apply(lambda x: (directory / x.split("/")[-1]))
#     df["in_current_repo"] = df["project_dir"].apply(lambda x: x.exists())
#     available = df.loc[df.in_current_repo].copy()
#     available["size"] = available["data_dir_path"].apply(lambda x: x.stat().st_size)
#     return available
