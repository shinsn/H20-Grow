"""
Gia James & Shinny No
Final Project for CPTR 215 Fundamentals of Software Design
Water Intake Tracker


references:
    styling in qt: https://doc.qt.io/qt-6/stylesheet.html
    pop with index: https://www.geeksforgeeks.org/python-list-pop-method/
    all about qtWidgets: https://www.pythonguis.com/tutorials/pyside6-widgets/
    line chart example: https://doc.qt.io/qtforpython-6/examples/example_charts_linechart.html
    is not None error handling: https://stackoverflow.com/questions/51664292/python-attributeerror-nonetype-object-has-no-attribute-text
    qcharts: https://doc.qt.io/qtforpython-6/PySide6/QtCharts/index.html
    plotting in charts: https://www.pythonguis.com/tutorials/pyside6-plotting-pyqtgraph/
    LABS: shopping lab, thermal converter lab
    event handling: https://www.pythonguis.com/tutorials/pyside6-signals-slots-events/
    all about tableWidgets: https://doc.qt.io/qt-6/qtablewidget.html
    alerts: https://www.pythonguis.com/tutorials/pyside6-dialogs/
    double validator: https://doc.qt.io/qt-6/qdoublevalidator.html
    strptime function: https://www.programiz.com/python-programming/datetime/strptime
    documentation about currentrow() in python/qt: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QListWidget.
    
BUGGS:
    - Unable to hit enter instead of the checkmark button for the set daily goal
    - Able to enter an invalid input to the daily logs, it doesnt save, but until the user closes and opens the app again they will be
    able to see the invalid input that is showing up in the logs 

"""

from datetime import datetime
import os
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QDateEdit,
    QMessageBox,
)
from PySide6.QtGui import QFont, QPixmap, QDoubleValidator, QPainter
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QPieSeries,
    QPieSlice,
    QValueAxis,
)


class H2OGrowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H2O Grow")
        self.setGeometry(100, 100, 1200, 700)

        self.data_logs = []  # this stores all of the logs as dictionaries using the 

        # create centeral widget 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # main layout for the app
        main_layout = QVBoxLayout(central_widget)
        central_widget.setStyleSheet("background-color: #dfe3db;") 

        # header section of the layout
        title_label = QLabel("H2O Grow")
        title_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #316047;") 
        main_layout.addWidget(title_label)

        # top section of the layout
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout, stretch=7)

        # left section of the layout 
        left_section = QVBoxLayout()
        top_layout.addLayout(left_section, stretch=3)

        # date selector
        date_layout = QHBoxLayout()
        water_log_label = QLabel("Water Log:")
        water_log_label.setFont(QFont("Arial", 10))
        water_log_label.setStyleSheet("color: #2d604b;")

        self.lineedit = QLineEdit()
        float_validator = QDoubleValidator()  # checks if input is float
        self.lineedit.setValidator(float_validator)
        self.lineedit.setMaxLength(6)  # input for water amt
        self.lineedit.setPlaceholderText("Enter Amt...")

        # calendar view of date
        self.date_pick = QDateEdit()
        self.date_pick.setDate(QDate.currentDate())
        self.date_pick.setMaximumDate(QDate.currentDate())
        self.date_pick.setCalendarPopup(True)
        self.date_pick.dateChanged.connect(self.update_logs_for_curr_day)

        # unit picker (dropdown)
        self.pick_units = QComboBox()
        self.pick_units.addItems(
            ["Fl Oz", "Cups", "Pints", "Quarts", "Gallons", "Liters"]
        )

        date_layout.addWidget(water_log_label)

        date_layout.addWidget(self.date_pick)
        date_layout.addWidget(self.lineedit)
        date_layout.addWidget(self.pick_units)
        left_section.addLayout(date_layout)

        # add and remove buttons 
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("+")
        self.add_button.setFont(QFont("Arial", 16))
        self.add_button.setStyleSheet(
            "background-color: #91cba9; color: #ffffff; border-radius: 5px;"
        )
        self.add_button.clicked.connect(self.add_log_entry)
        self.remove_button = QPushButton("-")
        self.remove_button.setFont(QFont("Arial", 16))
        self.remove_button.setStyleSheet(
            "background-color: #91cba9; color: #ffffff; border-radius: 5px;"
        )
        self.remove_button.clicked.connect(self.remove_log_entry)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        left_section.addLayout(button_layout)

        # log table 
        self.log_table = QTableWidget(0, 3)  # 5 rows, 3 columns
        self.log_table.setHorizontalHeaderLabels(["Time", "Amount", "Unit"])
        self.log_table.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #91cba9;"
        )
        self.log_table.itemSelectionChanged.connect(self.edit_log)
        self.log_table.cellChanged.connect(self.edit_log)
        self.value_set = []
        left_section.addWidget(self.log_table)

        # middle section of layout 
        middle_section = QVBoxLayout()

        top_layout.addLayout(middle_section, stretch=5)

        # begin creating the daily bar chart 
        self.daily_data_points = QBarSeries()
        self.daily_graph = QChart()
        self.daily_graph.legend().hide()
        self.daily_graph.setTitle("Daily Water Intake")

        self.daily_axisX = QBarCategoryAxis()
        self.daily_axisX.setTitleText("Hours")
        self.daily_axisX.append(
            [str(hour) for hour in range(24)]
        )
        self.daily_graph.addAxis(self.daily_axisX, Qt.AlignmentFlag.AlignBottom)

        self.daily_axisY = QValueAxis() 
        self.daily_axisY.setTitleText("Water Intake (Fl Oz)")
        self.daily_axisY.setRange(0, 40)
        self.daily_graph.addAxis(self.daily_axisY, Qt.AlignmentFlag.AlignLeft)

        self.daily_graph.addSeries(self.daily_data_points)
        self.daily_data_points.attachAxis(self.daily_axisX)
        self.daily_data_points.attachAxis(self.daily_axisY)

        self.daily_chart_view = QChartView(self.daily_graph)
        self.daily_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        chart_tabs = QTabWidget()
        chart_tabs.addTab(self.daily_chart_view, "Daily")

        # begin creating the weekly bar chart 
        self.weekly_bar_series = QBarSeries()
        self.weekly_graph = QChart()
        self.weekly_graph.legend().hide()
        self.weekly_graph.setTitle("Weekly Water Intake")

        self.weekly_axisX = QBarCategoryAxis()
        self.weekly_axisX.setTitleText("Days of the Week")
        self.weekly_axisX.append(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        self.weekly_graph.addAxis(self.weekly_axisX, Qt.AlignmentFlag.AlignBottom)

        self.weekly_axisY = QValueAxis()
        self.weekly_axisY.setTitleText("Water Intake (Fl Oz)")
        self.weekly_axisY.setRange(0, 10) 
        self.weekly_graph.addAxis(self.weekly_axisY, Qt.AlignmentFlag.AlignLeft)

        self.weekly_graph.addSeries(self.weekly_bar_series)
        self.weekly_bar_series.attachAxis(self.weekly_axisX)
        self.weekly_bar_series.attachAxis(self.weekly_axisY)

        self.weekly_chart_view = QChartView(self.weekly_graph)
        self.weekly_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        chart_tabs.addTab(self.weekly_chart_view, "Weekly")

        # begin setting up the monthly bar chart 
        self.monthly_bar_series = QBarSeries()
        self.monthly_graph = QChart()
        self.monthly_graph.legend().hide()
        self.monthly_graph.setTitle("Yearly Water Intake (Monthly Breakdown)")

        self.monthly_axisX = QBarCategoryAxis()
        self.monthly_axisX.setTitleText("Months")
        self.monthly_axisX.append([
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ])
        self.monthly_graph.addAxis(self.monthly_axisX, Qt.AlignmentFlag.AlignBottom)

        self.monthly_axisY = QValueAxis()
        self.monthly_axisY.setTitleText("Water Intake (Fl Oz)")
        self.monthly_axisY.setRange(0, 10)
        self.monthly_graph.addAxis(self.monthly_axisY, Qt.AlignmentFlag.AlignLeft)

        self.monthly_graph.addSeries(self.monthly_bar_series)
        self.monthly_bar_series.attachAxis(self.monthly_axisX)
        self.monthly_bar_series.attachAxis(self.monthly_axisY)

        self.monthly_chart_view = QChartView(self.monthly_graph)
        self.monthly_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_tabs.addTab(self.monthly_chart_view, "Monthly")

        # begin setting up the yearly bar chart 
        self.yearly_bar_series = QBarSeries()

        self.yearly_graph = QChart()
        self.yearly_graph.legend().hide()
        self.yearly_graph.setTitle("Total Water Intake by Year")

        self.yearly_axisX = QBarCategoryAxis()
        self.yearly_axisX.setTitleText("Years")
        self.yearly_graph.addAxis(self.yearly_axisX, Qt.AlignmentFlag.AlignBottom)

        self.yearly_axisY = QValueAxis()
        self.yearly_axisY.setTitleText("Water Intake (Fl Oz)")
        self.yearly_axisY.setRange(0, 10) 
        self.yearly_graph.addAxis(self.yearly_axisY, Qt.AlignmentFlag.AlignLeft)

        self.yearly_graph.addSeries(self.yearly_bar_series)
        self.yearly_bar_series.attachAxis(self.yearly_axisX)
        self.yearly_bar_series.attachAxis(self.yearly_axisY)

        self.yearly_chart_view = QChartView(self.yearly_graph)
        self.yearly_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        chart_tabs.addTab(self.yearly_chart_view, "Yearly")
        chart_tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #91cba9; }
            QTabBar::tab { background: #d8e8d8; padding: 8px; border: 1px solid #91cba9; }
            QTabBar::tab:selected { background: #91cba9; color: #ffffff; }
        """
        )

        middle_section.addWidget(chart_tabs)

        # right section of layout
        right_section = QVBoxLayout()
        top_layout.addLayout(right_section, stretch=2)

        # daily water goal
        goal_layout = QVBoxLayout()

        holder_for_goal_tile = QHBoxLayout()

        daily_goal_label = QLabel("Daily Water Goal:")
        daily_goal_label.setFont(QFont("Arial", 14))
        daily_goal_label.setStyleSheet("color: #2d604b;")
        holder_for_goal_tile.addWidget(daily_goal_label)

        self.water_goal_set = QLabel("64")
        self.water_goal_set.setFont(QFont("Arial", 14))
        self.water_goal_set.setStyleSheet("color: #2d604b;")
        self.unit_water_goal = QLabel("Fl Oz")
        self.unit_water_goal.setFont(QFont("Arial", 14))
        self.unit_water_goal.setStyleSheet("color: #2d604b;")
        holder_for_goal_tile.addWidget(self.water_goal_set)
        holder_for_goal_tile.addWidget(self.unit_water_goal)

        goal_layout.addLayout(holder_for_goal_tile)

        goal_and_units = QHBoxLayout()

        self.daily_goal_input = QLineEdit()
        self.daily_goal_input.setFixedWidth(100)
        self.daily_goal_input.setPlaceholderText("Enter goal...")
        self.daily_goal_input.setValidator(
            float_validator
        )  # from when we used it for logging; checking valid input
        self.daily_goal_input.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #91cba9;"
        )
        goal_and_units.addWidget(self.daily_goal_input)

        self.confirm_set_goal = QPushButton(
            "✓"
        )  # sends alert to user asking to confirm they want to change the goal
        self.confirm_set_goal.clicked.connect(self.set_water_goal)
        self.confirm_set_goal.setStyleSheet(
            "background-color: #91cba9; color: #ffffff; border-radius: 5px;"
        )
        self.confirm_set_goal.setFixedWidth(25)
        goal_and_units.addWidget(self.confirm_set_goal)

        # another dropdown for units; for goal input
        self.units_for_goal = QComboBox()
        self.units_for_goal.addItems(
            ["Fl Oz", "Cups", "Pints", "Quarts", "Gallons", "Liters"]
        )
        goal_and_units.addWidget(self.units_for_goal)

        goal_layout.addLayout(goal_and_units)

        right_section.addLayout(goal_layout)

        # plant picture  
        plant_image_path = (
            r"cute-cartoon-home-plant-in-clay-pot-illustration-vector.jpg"
        )
        self.plant_image_placeholder = QLabel()
        self.plant_image_placeholder.setPixmap(
            QPixmap(plant_image_path).scaled(
                200, 200, Qt.AspectRatioMode.KeepAspectRatio
            )
        )
        self.plant_image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plant_image_placeholder.setStyleSheet(
            "background-color: #ffffff; border-radius: 5px; padding: 5px; margin:10px;"
        )
        right_section.addWidget(self.plant_image_placeholder, stretch=2)

        # pie chart 1 (daily water intake)
        self.pie_chart1_container = QVBoxLayout()
        self.water_progress_pie_chart = QChart()
        self.water_progress_pie_chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.pie_chart_view = QChartView(self.water_progress_pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.series1 = QPieSeries()
        self.water_goal_reached = 0
        self.how_much_of_goal_left = 1 - self.water_goal_reached
        self.series1.append("Drank", self.water_goal_reached)
        self.series1.append("To Drink", self.how_much_of_goal_left)
        self.series1.setHoleSize(0.35)

        self.slice1 = self.series1.slices()[0]
        self.slice1.setColor("#316047")

        self.slice2 = self.series1.slices()[1]
        self.slice2.setColor("#b6c6b7")
        self.center_label = QLabel("50%")
        self.center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_label.setStyleSheet(
            """
            font-size: 1px;
            color: #316047;
            background-color: transparent;
        """
        )
        self.progress_label = QLabel("0")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.water_progress_pie_chart.addSeries(self.series1)
        self.pie_chart1_container.addWidget(self.pie_chart_view)
        self.pie_chart1_container.addWidget(self.progress_label)

        # Pie Chart 2 (plant succcess rate)
        self.pie_chart2_container = QVBoxLayout()
        self.plant_pie_chart = QChart()
        self.plant_pie_chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.pie_chart_view2 = QChartView(self.plant_pie_chart)
        self.pie_chart_view2.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.series2 = QPieSeries()
        self.series2.setHoleSize(0.35)
        self.slice2_1 = QPieSlice("Total", 10)
        self.slice2_1.setColor("#316047")

        self.slice2_2 = QPieSlice("Alive", 90)
        self.slice2_2.setColor("#b6c6b7")

        self.series2.append(self.slice2_1)
        self.series2.append(self.slice2_2)

        self.plant_pie_chart.addSeries(self.series2)
        self.pie_chart2_container.addWidget(self.pie_chart_view2)

        right_section.addLayout(self.pie_chart1_container)
        right_section.addLayout(self.pie_chart2_container)

        self.pie_chart_view.setMinimumSize(250, 250) 
        self.pie_chart_view2.setMinimumSize(250, 250)
        # setting focus on water input line for calender doesn't get highlighted
        self.lineedit.setFocus()
        self.load_logs()


    def add_log_entry(self):
        """gets the water amount, unit, and date from input section.
        gets the current time from QTime.
        sends a message to the user if the input amount is less than or equal to 0
        if it is valid input; create a dictionary called new_log, and appends that to data_logs (list of dictionaries)
        -> calls functions "update_logs_for_curr_day" and "save_logs"
        clears the input lineedit
        """
        water_amt = self.lineedit.text()
        units = self.pick_units.currentText()
        current_date = self.date_pick.date().toString("yyyy-MM-dd")
        current_time = QTime.currentTime()
        if water_amt and water_amt != "." and float(water_amt) > 0:
            new_log = {
                "date": current_date,  
                "time": current_time.toString("hh:mm:ss AP"),
                "amount": water_amt,
                "unit": units,
            }
            self.data_logs.append(new_log)
            self.update_logs_for_curr_day()
            self.save_logs()
        else:
            QMessageBox.warning(
                self,
                "Invalid Input Amount",
                "Please Enter a Valid Input",
                QMessageBox.StandardButton.Close,
            )
        self.lineedit.clear()


    def update_logs_for_curr_day(self):
        """this will only show the logs for the currently selected day, if there are any
        goes through the main list (data_logs) of dictionaries, see if the date value is equal
        to the date the user picked on the calendar; if there is a math, appends it to new list
        -> calls "update_log_table" function, passes new list as parameter
        -> calls "update_daily_chart" so that the all other graphs can be updated 
        """
        self.filtered_logs = []
        for i in range(len(self.data_logs)):
            if self.data_logs[i]["date"] == self.date_pick.date().toString(
                "yyyy-MM-dd"
            ):
                self.filtered_logs.append(self.data_logs[i])
        self.update_log_table(self.filtered_logs)
        self.update_daily_chart()


    def update_log_table(self, log):
        """iterates through a log (data_log, filter_log) adds to table
        puts in the values of each dictionary log in list of logs/(dictionaries)
        calls "update_daily_chart" so that all the charts are updated
        """
        self.log_table.setRowCount(len(log))
        for row, log_entry in enumerate(log):
            self.log_table.setItem(row, 0, QTableWidgetItem(log_entry["time"]))
            self.log_table.setItem(row, 1, QTableWidgetItem(str(log_entry["amount"])))
            self.log_table.setItem(row, 2, QTableWidgetItem(log_entry["unit"]))

        self.log_table.setColumnWidth(0, 150)
        self.log_table.setColumnWidth(1, 100)
        self.log_table.setColumnWidth(2, 200)

        self.update_daily_chart()

    def edit_log(self):
        """ finds the cell that was edited; calls the save_logs if the edited water_amt is valid float 
        calls "update_daily_chart" so that all the charts are updated
        """
        edited_water_amt = self.log_table.currentItem()
        if edited_water_amt is not None:
            if is_float(edited_water_amt.text()):
                row = edited_water_amt.row()
                time = self.log_table.item(row, 0).text()
                for i in range(len(self.data_logs)):
                    if time == self.data_logs[i]["time"]:
                        self.data_logs[i]["amount"] = edited_water_amt.text()
                        self.save_logs()
                        self.update_daily_chart()


    def update_pie_chart(self):
        """ takes log parameter, so we know which list of dictionaries we should be calculating with
            pie chart 1 : should add up all the amount of water the user inputted, convert to fl oz (CALLS HELPER FUNCTION)
                          and divide that by the goal that the user set, or the default goal, that decimal will
                          be how much of our water goal that we reached
        """
        total_intake = 0
        selected_date = self.date_pick.date().toString("yyyy-MM-dd")
        # only add water amounts if they fall in the date that is the currently selected date
        for log_entry in self.data_logs:
            if log_entry["date"] == selected_date:
                converted_amt = convert_to_oz(log_entry["amount"], log_entry["unit"])
                total_intake += float(converted_amt)
        goal_to_convert = float(self.water_goal_set.text())
        goal = convert_to_oz(goal_to_convert, self.units_for_goal.currentText())
        self.progress = total_intake / goal
        if total_intake >= goal:
            self.water_goal_reached = 1
            self.how_much_of_goal_left = 0
        else:
            self.water_goal_reached = self.progress
            self.how_much_of_goal_left = 1 - self.water_goal_reached
        
        self.progress_percentage = self.progress * 100
        self.progress_label.setText(f'{self.progress_percentage:.2f}% of goal met')

        # update pie series with the new numbers
        self.series1.clear()
        self.series1.append("Drank", self.water_goal_reached)
        self.series1.append("To Drink", self.how_much_of_goal_left)

        # redecorate w colors
        self.slice1 = self.series1.slices()[0]
        self.slice1.setColor("#316047")
        self.slice2 = self.series1.slices()[1]
        self.slice2.setColor("#b6c6b7")


    def update_goal_pie_chart(self):
        """Update the bottom pie chart to show how many days the user met their water goal in the selected month.
        ->calls "convert_to_oz" to make sure all entries are compatible 
        <- this gets called in the "update_daily_chart" function like all the other graphs
        """
        
        selected_date = self.date_pick.date()
        current_month = selected_date.month()
        current_year = selected_date.year()

        daily_totals = {}
        for log_entry in self.data_logs:
            log_date = QDate.fromString(log_entry["date"], "yyyy-MM-dd")
            if log_date.year() == current_year and log_date.month() == current_month:
                day = log_date.day()
                if day not in daily_totals:
                    daily_totals[day] = 0
                daily_totals[day] += convert_to_oz(log_entry["amount"], log_entry["unit"])

        goal_in_fl_oz = convert_to_oz(float(self.water_goal_set.text()), self.unit_water_goal.text()) # calculate met and missed goals
        days_in_month = QDate(current_year, current_month, 1).daysInMonth()
        met_goal = sum(1 for total in daily_totals.values() if total >= goal_in_fl_oz)
        missed_goal = days_in_month - met_goal

        # update the pie charts 2 slices defined in the initalizer/constructor 
        self.series2.clear()
        self.series2.append("Met", met_goal)
        self.series2.append("Missed", missed_goal)

        # redecorate w colors
        slice_met = self.series2.slices()[0]
        slice_met.setColor("#316047") 
        slice_missed = self.series2.slices()[1]
        slice_missed.setColor("#b6c6b7") 

        slice_met.setLabel(f"Met: {met_goal} days")
        slice_missed.setLabel(f"Missed: {missed_goal} days")


    def update_daily_chart(self):
        """Update the daily chart to show water intake per hour for the current day as a bar graph. This is 
        in military time from 0-24 each day
        -> calls "time_to_float" to conver the time to a hourly representation
        -> calls "converted_to_oz" to have the data display correctly in one unit"""

        selected_date = self.date_pick.date().toString("yyyy-MM-dd")

        hourly_data = {hour: 0 for hour in range(24)}  # this initializes all hours to 0 at first 

        # find logs for the selected date and enter hourly_data
        for log_entry in self.data_logs:
            if (log_entry["date"] == selected_date):
                    hour = time_to_float(log_entry["time"]) #takes the time of the the entry using the "time" key from the dictioary in data_logs
                    y = convert_to_oz(log_entry["amount"], log_entry["unit"])
                    hourly_data[hour] += y #adds the amount of oz to the hourly data dictionary for that hour

        # clear existing bar sets in the series
        self.daily_data_points.clear()

        # create a new bar set for the day
        bar_set = QBarSet("Water Intake")
        bar_set.setColor("#316047")
        for hour in range(24):
            bar_set.append(hourly_data[hour])  # Add data for each hour (0-23)

        self.daily_data_points.append(bar_set)

        # this creates a dynamicly updated range of data for the y axis according the amount that the user has drank
        max_value = max(hourly_data.values()) 
        self.daily_axisY.setRange(0, max(max_value * 1.2, 10))

        # call all other functions so whenever the update daily chart gets updated all the other graphs do too
        self.update_monthly_chart()
        self.update_weekly_chart()
        self.update_yearly_chart()
        self.update_pie_chart()
        self.update_goal_pie_chart()
 
    def update_weekly_chart(self):
        """Update the weekly chart to show total water intake for each day of the week."""

        current_date = self.date_pick.date()
        start_of_week = current_date.addDays(-(current_date.dayOfWeek() % 7))  # changes the date used to a sunday so the user can see the current week not just 7 days after the 
        
        #initializes all days water intake to be 0 at first 
        weekly_data = {day: 0 for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}

        # filter logs for the current week and calculate total intake for each day
        for log_entry in self.data_logs:
            log_date = QDate.fromString(log_entry["date"], "yyyy-MM-dd")
            if log_date >= start_of_week and log_date < start_of_week.addDays(7):
                day_name = log_date.toString("dddd")  # Get the day name (e.g., "Monday") dddd is specific to Qt.Date.toString
                amount_oz = convert_to_oz(log_entry["amount"], log_entry["unit"])
                weekly_data[day_name] += amount_oz
        self.weekly_bar_series.clear()
        bar_set = QBarSet("Water Intake")
        bar_set.setColor("#91cba9")
        for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            bar_set.append(weekly_data[day])

        self.weekly_bar_series.append(bar_set)

        max_value = max(weekly_data.values())
        self.weekly_axisY.setRange(0, max(max_value * 1.2, 10))


    def update_monthly_chart(self):
        """Update the monthly chart to show total water intake for each month of the current year."""
        # get current year from the date picker
        selected_date = self.date_pick.date()
        current_year = selected_date.year()
        monthly_data = {month: 0 for month in range(1, 13)} # sets all months to 0

        # find water intake by month
        for log_entry in self.data_logs:
            log_date = QDate.fromString(log_entry["date"], "yyyy-MM-dd")
            if log_date.year() == current_year: 
                month = log_date.month()  # gets month as an integer (1 = January)
                amount_oz = convert_to_oz(log_entry["amount"], log_entry["unit"])
                monthly_data[month] += amount_oz

        self.monthly_bar_series.clear()
        bar_set = QBarSet("Water Intake")
        bar_set.setColor("#2d604b") 
        for month in range(1, 13):
            bar_set.append(monthly_data[month])  # add total intake for each month
        self.monthly_bar_series.append(bar_set)

        # Update the Y-axis range dynamically
        max_value = max(monthly_data.values(), default=0)
        self.monthly_axisY.setRange(0, max(max_value * 1.2, 10))


    def update_yearly_chart(self):
        """Update the yearly chart to show total water intake for each year in the dataset."""
        yearly_data = {}
        for log_entry in self.data_logs:
            log_date = QDate.fromString(log_entry["date"], "yyyy-MM-dd")
            if log_date.isValid():
                year = log_date.year()
                amount_oz = convert_to_oz(log_entry["amount"], log_entry["unit"])
                if year not in yearly_data:
                    yearly_data[year] = 0
                yearly_data[year] += amount_oz
        self.yearly_bar_series.clear()
        bar_set = QBarSet("Water Intake")
        bar_set.setColor("#b6c6b7")
        years = sorted(yearly_data.keys())  # sort years for display
        for year in years:
            bar_set.append(yearly_data[year])
        self.yearly_bar_series.append(bar_set)
        # update lables for x-axis
        self.yearly_axisX.clear()
        self.yearly_axisX.append([str(year) for year in years])

        max_value = max(yearly_data.values(), default=0)
        self.yearly_axisY.setRange(0, max(max_value * 1.2, 10))


    def remove_log_entry(self):
        """Remove the selected log entry from the table and data logs."""
        selected_row = self.log_table.currentRow()  # get the selected row in the table using this built in list function
        if selected_row >=0:
            log_to_remove = self.filtered_logs.pop(selected_row)
            self.data_logs = [log for log in self.data_logs if log != log_to_remove]

            self.update_log_table(self.filtered_logs)
            self.save_logs()
        else:
            log_to_remove = self.filtered_logs.pop(-1)
            self.data_logs = []

        
        self.update_daily_chart()

    def set_water_goal(self):
        """sets the header label to be the goal the user entered
        takes the flaot input, and the units from the dropdown,
        if the input is valid, updates header (the label above the input line)
        then clear the input line
        """
        confirm = QMessageBox.question(
            self,
            "Set Goal",
            "Confirm Set Goal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.water_goal_amt = self.daily_goal_input.text()
            if float(self.water_goal_amt) <= 0:
                QMessageBox.warning(
                    self,
                    "Invalid Goal Amount",
                    "Please Enter a Valid Goal",
                    QMessageBox.StandardButton.Close,
                )
            else:
                self.water_goal_unit = self.units_for_goal.currentText()
                if self.water_goal_amt and self.water_goal_amt != ".":
                    self.water_goal_set.setText(f"{self.water_goal_amt}")
                    self.unit_water_goal.setText(f"{self.water_goal_unit}")
                    self.update_logs_for_curr_day()
            self.daily_goal_input.clear()

    def save_logs(self):
        """saves logs in txt file for persistence,
        uses the logs in data_logs, not just the logs shown in the table.
        logs by date is each dictionary in the data_logs list. if a date in data_logs
        is not a alr in logs_by_date, create key--which is the date-- with a value that is an empty list.
        in that empty list, append ductionary with time, amount, and unit.
        if date already DOES exist in logs_by_date--for example, if there are multiple inputs for one day, it
        will just append its a ductionary to the already existing list
        creates or edit txt file and fills it with the dictionaries
        """
        logs_by_date = {}
        for log in self.data_logs:
            date = log["date"]
            if date not in logs_by_date:
                logs_by_date[date] = []
            logs_by_date[date].append(
                {"time": log["time"], "amount": log["amount"], "unit": log["unit"]}
            )
        with open("logs.txt", "w") as file:
            for date, entries in logs_by_date.items():
                file.write(f"{date}:\n")
                for entry in entries:
                    file.write(f"  {entry}\n")

    def load_logs(self):
        """loads prev inputted logs that the user entered from txt file.
        gets the date (key) and values from file; uses it to create log_entries to append to data_logs (our main log holder)
        DATA_LOGS should remain unchanged, create new lists for the filtering stuff
        append log_entry to data_loh regardless, but if the log matches the current date pick, add it to a new "filtered" list
        passes that filtered list to update_log_table function
        """
        if os.path.exists("logs.txt"):
            self.data_logs=[]
            self.loaded_but_filtered = []
            with open("logs.txt", "r") as file:
                lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line.endswith(":"):
                    current_date = line[:-1]  # removing the : from (ex: 2024-12-10":"")
                elif current_date and line.startswith("{") and line.endswith("}"):  # the {...} inside a time thing
                    entry = eval(line)  # turns the string dict to actaul python dict!!
                    log_entry = {
                        "date": current_date,
                        "time": entry["time"],
                        "amount": entry["amount"],
                        "unit": entry["unit"],
                    }
                    self.data_logs.append(log_entry)
                    if current_date == self.date_pick.date().toString("yyyy-MM-dd"):
                        self.loaded_but_filtered.append(log_entry)
            self.update_log_table(self.loaded_but_filtered)

    def keyPressEvent(self, event):
        """Handle key press events for Enter and Delete keys."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.add_log_entry()
            self.update_daily_chart()
        elif event.key() == Qt.Key_Delete or event.key() == Qt.Backspace:
            self.remove_log_entry()
            self.update_daily_chart()


def convert_to_oz(x: float, scale: str) -> float:
    """convers all units to fl oz, our main unit that we will use to graph;
    float(x) bc getting errors that x was str otherwise
    "Fl Oz", "Cups", "Pints", "Quarts", "Gallons", "Liters"
    >>> convert_to_oz(5.00, "Fl Oz")
    5.0
    >>> convert_to_oz(12.12, "Cups")
    96.96
    >>> convert_to_oz(1, "Quarts")
    32.0
    >>> convert_to_oz(4.3, "Pints")
    68.8
    >>> convert_to_oz(13, "Gallons")
    1664.0
    >>> convert_to_oz(4, "Liters")
    135.256
    """
    if scale == "Fl Oz":
        oz = float(x)
    elif scale == "Cups":
        oz = float(x) * 8
    elif scale == "Pints":
        oz = float(x) * 16
    elif scale == "Quarts":
        oz = float(x) * 32
    elif scale == "Gallons":
        oz = float(x) * 128
    elif scale == "Liters":
        oz = float(x) * 33.814
    return oz


def time_to_float(time_str):
    """takes a string time (e.g 03:14:12 PM) and turns it into datetime object
    time_str is in format %I for hour (in 12 hour format) %M (minutes) and %S (seconds) and %p (AM/PM)
    >>> time_to_float("04:00:00 PM")
    16
    >>> time_to_float("02:30:10 AM")
    2
    >>> time_to_float("07:45:50 AM")
    7
    >>> time_to_float("12:30:50 PM")
    12
    """
    time_obj = datetime.strptime(time_str, "%I:%M:%S %p")
    return time_obj.hour

def is_float(string: str) -> bool:
    """ helper function for validating the value in 'amount' in our table logs,
        we only want edit logs to execute if the user is editing a number under amount, this function checks if a string
        can we a float (ex: '234') returns TRUE; 'fl oz' would return FALSE
        >>> is_float('12')
        True
        >>> is_float('2.3')
        True
        >>> is_float('test')
        False
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    app = QApplication(sys.argv)

    window = H2OGrowApp()
    window.show()

    sys.exit(app.exec())

