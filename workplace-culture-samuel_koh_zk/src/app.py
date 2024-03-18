import os
import pandas as pd
import plotly
import plotly.offline as py_offline
import sys
import tempfile
import webbrowser

import tkinter as tk
from loguru import logger
from threading import Thread
from tkinter import messagebox
from tkinter import Toplevel
from tkinter import ttk

from work_culture.model import TopicModelingPipeline
from work_culture.docx_to_csv import docx_to_csv
from work_culture.utils import count_duplicates, topic_aggregation


def get_data_path() -> str:
    """Determines the path to the data directory.

    Returns:
        str: The absolute path to the directory containing data files.
    """
    base_path = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(__file__)
    )
    return os.path.join(base_path, "..", "data")


class App(tk.Tk):
    """A GUI application designed for topic modeling tasks.

    This application provides a user-friendly interface for converting DOCX files to CSV,
    selecting files for analysis, specifying topic modeling parameters, and viewing results.
    It supports operations such as file conversion, model training, detailed information display,
    hierarchy visualization, and subset comparison.
    """

    def __init__(self):
        """Initializes the application with a predefined window size and title, and sets up the GUI components."""
        super().__init__()
        self.geometry("1400x500")
        self.title("Topic Modeler")
        self.data_path = get_data_path()
        self._init_vars()
        self._create_widgets()

    def _init_vars(self):
        """Initializes the variables used for Tkinter widgets and model control."""
        self.option_var = tk.StringVar(self)
        self.first_subset_var = tk.StringVar(self)
        self.second_subset_var = tk.StringVar(self)
        self.num_topics_var = tk.StringVar(self)
        self.docx_file_var = tk.StringVar(self)
        self.result_var = tk.StringVar(self)
        # self.neighbours_var = tk.StringVar(self)
        self.selected_topics_var = tk.StringVar(self)
        self.filename_var = tk.StringVar(self)
        self.model_status_var = tk.StringVar(self)
        self.model_status_var.set("Model not started")
        self.model = None

    def _create_widgets(self):
        """Creates and arranges all GUI components within the application window."""
        paddings = {"padx": 5, "pady": 8}
        self._docx_to_csv(paddings)
        self._setup_file_selection(paddings)
        self._setup_topic_input(paddings)
        self._setup_model_status(paddings)
        self._setup_additional_controls(paddings)
        self._update_button_states()
        self._setup_output_controls(paddings)
        self._compare_subsets(paddings)

    def _docx_to_csv(self, paddings, row=0):
        """Sets up the UI for initial conversion from DOCX to CSV."""
        ttk.Label(self, text="Convert DOCX to CSV:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        self.docx_file_options = self._update_file_options("docx")
        self.docx_file_var.set(
            self.docx_file_options[0]
            if self.docx_file_options
            else "No DOCX files found"
        )
        self.docx_file_menu = ttk.OptionMenu(
            self, self.docx_file_var, self.docx_file_var.get(), *self.docx_file_options
        )
        self.docx_file_menu.grid(column=1, row=row, sticky=tk.W, **paddings)
        ttk.Button(self, text="Convert to CSV", command=self._convert_docx_to_csv).grid(
            column=2, row=row, sticky=tk.W, **paddings
        )
        ttk.Button(
            self, text="Refresh DOCX List", command=self._refresh_docx_file_options
        ).grid(column=3, row=row, sticky=tk.W, **paddings)

    def _refresh_docx_file_options(self):
        """Refreshes the list of DOCX files in the option menu."""
        self.docx_file_options = self._update_file_options("docx")
        self.docx_file_var.set(
            self.docx_file_options[0]
            if self.docx_file_options
            else "No DOCX files found"
        )
        menu = self.docx_file_menu["menu"]
        menu.delete(0, "end")
        for option in self.docx_file_options:
            menu.add_command(
                label=option, command=lambda value=option: self.docx_file_var.set(value)
            )

    def _setup_file_selection(self, paddings, row=1):
        """Sets up the file selection UI components."""
        ttk.Label(self, text="Select the file you want analysed:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        self.file_options = self._update_file_options("csv")
        self.option_menu = ttk.OptionMenu(
            self, self.option_var, self.file_options[0], *self.file_options
        )
        self.option_menu.grid(column=1, row=row, sticky=tk.W, **paddings)
        ttk.Button(
            self,
            text="Refresh File List",
            command=lambda: self._refresh_file_options("csv"),
        ).grid(column=2, row=row, sticky=tk.W, **paddings)

    def _setup_topic_input(self, paddings, row=2):
        """Sets up the topic and neighbour input UI components."""
        ttk.Label(self, text="Enter the number of topics you want:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        ttk.Entry(self, textvariable=self.num_topics_var).grid(
            column=1, row=row, sticky=tk.W, **paddings
        )
        # ttk.Label(self, text="Enter the number of neighbours:").grid(
        #     column=2, row=row, sticky=tk.W, **paddings
        # )
        # ttk.Entry(self, textvariable=self.neighbours_var).grid(
        #     column=3, row=row, sticky=tk.W, **paddings
        # )
        ttk.Button(self, text="Train model", command=self._run_model).grid(
            column=2, row=row, sticky=tk.W, **paddings
        )

    def _setup_model_status(self, paddings, row=3):
        """Sets up the UI component for displaying the model training status."""
        ttk.Label(self, text="Model training status:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        ttk.Label(self, textvariable=self.model_status_var).grid(
            column=1, row=row, sticky=tk.W, **paddings
        )

    def _setup_additional_controls(self, paddings, row=4):
        """Sets up additional control UI components for detailed information and topic hierarchies."""
        ttk.Label(self, text="Select the information you would like to see:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        self.detailed_info_button = ttk.Button(
            self,
            text="Detailed topic info dataframe",
            command=self._detailed_info_dataframe,
        )
        self.detailed_info_button.grid(column=1, row=row, sticky=tk.W, **paddings)
        self.hierarchy_button = ttk.Button(
            self,
            text="Hierarchically reducing topics",
            command=self._hierarchy_reduction,
        )
        self.hierarchy_button.grid(column=2, row=row, sticky=tk.W, **paddings)
        self.barchart_button = ttk.Button(
            self,
            text="Barchart representation",
            command=self._bar_chart,
        )
        self.barchart_button.grid(column=3, row=row, sticky=tk.W, **paddings)
        # self.top_topics_button = ttk.Button(
        #     self,
        #     text="Top topics",
        #     command=self._topics,
        # )
        # self.top_topics_button.grid(column=4, row=row, sticky=tk.W, **paddings)

    def _setup_output_controls(self, paddings, row=5):
        """Sets up output control UI components."""
        ttk.Label(
            self, text="Enter the selected topics you want saved: (e.g., 1, 2, 3)"
        ).grid(column=0, row=row, sticky=tk.W, **paddings)
        ttk.Entry(self, textvariable=self.selected_topics_var).grid(
            column=1, row=row, sticky=tk.W, **paddings
        )
        ttk.Label(self, text="Enter desired output file name:").grid(
            column=2, row=row, sticky=tk.W, **paddings
        )
        ttk.Entry(self, textvariable=self.filename_var).grid(
            column=3, row=row, sticky=tk.W, **paddings
        )
        ttk.Button(self, text="Save CSV subset", command=self._csv_subset).grid(
            column=4, row=row, sticky=tk.W, **paddings
        )

    def _compare_subsets(self, paddings, row=6):
        """Sets up UI components to compare the number of similar comments between two subsets."""
        ttk.Label(self, text="Choose the first subset:").grid(
            column=0, row=row, sticky=tk.W, **paddings
        )
        self.first_subset_options = self._update_file_options("csv")
        self.first_subset_var.set(self.first_subset_options[0])
        self.first_subset_menu = ttk.OptionMenu(
            self,
            self.first_subset_var,
            self.first_subset_options[0],
            *self.first_subset_options,
        )
        self.first_subset_menu.grid(column=1, row=row, sticky=tk.W, **paddings)
        ttk.Label(self, text="Choose the second subset:").grid(
            column=2, row=row, sticky=tk.W, **paddings
        )
        self.second_subset_options = self._update_file_options("csv")
        self.second_subset_var.set(self.second_subset_options[0])
        self.second_subset_menu = ttk.OptionMenu(
            self,
            self.second_subset_var,
            self.second_subset_options[0],
            *self.second_subset_options,
        )
        self.second_subset_menu.grid(column=3, row=row, sticky=tk.W, **paddings)
        ttk.Button(self, text="Refresh Subsets", command=self._refresh_subsets).grid(
            column=4, row=row, sticky="W", **paddings
        )
        ttk.Button(
            self, text="Compare Subsets", command=self._update_comparison_result
        ).grid(column=5, row=row, sticky="W", **paddings)
        ttk.Label(self, textvariable=self.result_var).grid(
            column=0, row=7, sticky=tk.W, **paddings
        )

    def _update_file_options(self, type: str) -> list:
        """Updates and returns the list of file options based on the specified file type.

        This function filters files in the data directory according to the provided file type.
        If the directory is empty or no files match the specified types, a placeholder message is returned.

        Args:
            file_types (str): File extensions to filter by, e.g., ["csv", "docx"].

        Returns:
            List[str]: A list of file names matching the specified types, or a placeholder if none.
        """
        try:
            files = [f for f in os.listdir(self.data_path) if f.endswith(f".{type}")]
            return files if files else ["No files found"]
        except Exception as e:
            logger.error(f"Error accessing the data directory: {e}")
            return ["No files found"]

    def _update_button_states(self):
        """Updates the button states based on the model training status."""
        state = (
            "normal"
            if self.model_status_var.get() == "Model training done."
            else "disabled"
        )
        self.detailed_info_button["state"] = state
        self.hierarchy_button["state"] = state
        self.barchart_button["state"] = state
        # self.top_topics_button["state"] = state

    def _refresh_file_options(self, file_type):
        """Refreshes the list of files in the option menu."""
        self.file_options = self._update_file_options(file_type)
        self.option_menu["menu"].delete(0, "end")
        for option in self.file_options:
            self.option_menu["menu"].add_command(
                label=option, command=tk._setit(self.option_var, option)
            )
        self.option_var.set(
            self.file_options[0] if self.file_options else "No files found"
        )

    def _run_model(self):
        """Prepares model training environment and starts the training process in a new thread."""
        self.model_status_var.set("Model is training...")
        # Offload the training to a new thread to keep the UI responsive
        training_thread = Thread(target=self._start_model_training)
        training_thread.start()

    def _start_model_training(self):
        """Runs the model training process."""
        try:
            csv_path = os.path.join(self.data_path, self.option_var.get())
            df = pd.read_csv(csv_path)
            number_of_topics = int(self.num_topics_var.get())
            self.model = TopicModelingPipeline(nr_topics=number_of_topics)
            self.df = self.model.fit_model(df)
            self._update_model_status("Model training done.")
        except Exception as e:
            self._update_model_status("Model training failed.")
            logger.exception(f"Error during model training: {e}")

    def _update_model_status(self, message):
        """Updates the model status on the UI thread."""
        if self._is_threadsafe():
            self.model_status_var.set(message)
            self._update_button_states()
        else:
            self.after(100, self._update_model_status, message)

    def _is_threadsafe(self):
        """Checks if the current context is threadsafe (i.e., is the main thread)."""
        # Implement thread safety check depending on your application's architecture
        return True  # Placeholder

    def _detailed_info_dataframe(self):
        """Generates a detailed dataframe for the selected topics and displays it in a new Tkinter window."""
        try:
            df = self.model.print_details()
            if df is None or df.empty:
                messagebox.showerror(
                    "Error", "The print_details method did not return data."
                )
                return
            details_window = Toplevel(self)
            details_window.title("Detailed Information")
            details_window.geometry("1000x500")
            tree = ttk.Treeview(details_window)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb = ttk.Scrollbar(details_window, orient="vertical", command=tree.yview)
            vsb.pack(side="right", fill="y")
            tree.configure(yscrollcommand=vsb.set)
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"
            for col in df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            for _, row in df.iterrows():
                tree.insert("", "end", values=row.tolist())
        except Exception as e:
            messagebox.showerror("Error", f"Error visualizing details: {e}")

    def _hierarchy_reduction(self):
        """Displays the hierarchy visualization graph using Plotly in the default web browser."""
        try:
            fig = self.model.visualise_hierarchy()
            if fig is None:
                logger.error(
                    "The visualise_hierarchy method returned None. Expected a Plotly Figure instance."
                )
                messagebox.showerror(
                    "Error",
                    "Error visualizing hierarchy: The visualise_hierarchy method did not return a figure.",
                )
                return
            if not isinstance(fig, plotly.graph_objs._figure.Figure):
                logger.error(
                    f"Expected a Plotly Figure instance, got {type(fig)} instead."
                )
                messagebox.showerror(
                    "Error",
                    f"Error visualizing hierarchy: Unexpected return type from visualise_hierarchy.",
                )
                return
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            py_offline.plot(fig, filename=temp_file.name, auto_open=False)
            webbrowser.open("file://" + temp_file.name, new=2)
        except Exception as e:
            logger.exception("Error visualizing hierarchy")
            messagebox.showerror("Error", f"Error visualizing hierarchy: {e}")

    def _bar_chart(self):
        """Displays a barchart representation of the topics using Plotly in the default web browser."""
        try:
            fig = self.model.visualise_barchart()
            if fig is None:
                logger.error(
                    "The visualise_barchart method returned None. Expected a Plotly Figure instance."
                )
                messagebox.showerror(
                    "Error",
                    "Error visualizing barchart: The visualise_barchart method did not return a figure.",
                )
                return
            if not isinstance(fig, plotly.graph_objs._figure.Figure):
                logger.error(
                    f"Expected a Plotly Figure instance, got {type(fig)} instead."
                )
                messagebox.showerror(
                    "Error",
                    f"Error visualizing barchart: Unexpected return type from visualise_barchart.",
                )
                return
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            py_offline.plot(fig, filename=temp_file.name, auto_open=False)
            webbrowser.open("file://" + temp_file.name, new=2)
        except Exception as e:
            logger.exception("Error visualizing barchart")
            messagebox.showerror("Error", f"Error visualizing barchart: {e}")

    # TODO: Ignore for now
    def _topics(self):
        """Displays the top topics."""
        pass  # Placeholder for top topics display

    def _csv_subset(self):
        """Saves a CSV subset based on the selected topics."""
        selected_topics = list(map(int, self.selected_topics_var.get().split(",")))
        file_name = self.filename_var.get() + ".csv"
        save_path = os.path.join(self.data_path, file_name)
        topic_aggregation(save_path, selected_topics, self.df)
        logger.info(f"Saving CSV subset for topics: {selected_topics}")

    def _perform_subset_comparison(self):
        """Performs subset comparison and returns percentage duplicate relative to the smaller subset."""
        filepath_csv1 = os.path.join(self.data_path, self.first_subset_var.get())
        filepath_csv2 = os.path.join(self.data_path, self.second_subset_var.get())
        return count_duplicates(filepath_csv1, filepath_csv2)

    def _update_comparison_result(self) -> None:
        """
        Calls the subset comparison function and updates the UI with the comparison result.
        """
        try:
            result_percentage = self._perform_subset_comparison()
            # Format the result to display with two decimal places
            formatted_result = "{:.2f}".format(result_percentage)
            self.result_var.set(f"The percentage of duplicates is {formatted_result}%.")
            logger.info("Comparison completed successfully.")
        except Exception as e:
            self.result_var.set(
                "Error performing comparison. Check the log for details."
            )
            logger.error(f"Error performing comparison: {e}")

    def _convert_docx_to_csv(self):
        """Converts initial docx file to CSV file."""
        filepath = os.path.join(self.data_path, self.docx_file_var.get())
        savepath = os.path.join(self.data_path, "raw_comments.csv")
        docx_to_csv(filepath, savepath)

    def _refresh_subsets(self):
        """Refreshes both subset menus."""
        self.first_subset_options = self._update_file_options("csv")
        self.second_subset_options = self._update_file_options("csv")

        self.first_subset_menu["menu"].delete(0, "end")
        for option in self.first_subset_options:
            self.first_subset_menu["menu"].add_command(
                label=option,
                command=lambda value=option: self.first_subset_var.set(value),
            )
        self.second_subset_menu["menu"].delete(0, "end")
        for option in self.second_subset_options:
            self.second_subset_menu["menu"].add_command(
                label=option,
                command=lambda value=option: self.second_subset_var.set(value),
            )


if __name__ == "__main__":
    logger.add("app.log", rotation="1 week")
    app = App()
    app.mainloop()
