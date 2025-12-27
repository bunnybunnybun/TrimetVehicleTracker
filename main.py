import requests
import json
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
script_dir = os.path.dirname(os.path.abspath(__file__))

appID = "9BB16D426AE6D7BB1EDAED215"
routesUrl = f"https://developer.trimet.org/ws/V1/routeConfig?appID={appID}&json=true&dir=true&stops=1"


class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Trimet Bus Tracker")
        self.set_border_width(20)

        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(f"{script_dir}/style.css")
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.routes_data = []

        def getRoutes():
            self.routesResponse = requests.get(routesUrl).json()
            self.routes_data = self.routesResponse["resultSet"]["route"]

            for route in self.routes_data:
                self.route_dropdown.append_text(route["desc"])


        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.routesLabel = Gtk.Label(label="Select route:")
        self.route_dropdown = Gtk.ComboBoxText()
        self.route_dropdown.set_entry_text_column(0)
        self.route_dropdown.connect("changed", self.on_route_selected)

        self.stopsLabel = Gtk.Label(label="Select one of the stops along the route:")
        self.stop_dropdown = Gtk.ComboBoxText()
        self.stop_dropdown.connect("changed", self.on_stop_selected)

        self.arrivals_explanation_label = Gtk.Label(label="Arrivals:")
        self.arrivals_label = Gtk.Label()
        
        self.main_box.add(self.routesLabel)
        self.main_box.add(self.route_dropdown)
        self.main_box.add(self.stopsLabel)
        self.main_box.add(self.stop_dropdown)
        self.main_box.add(self.arrivals_explanation_label)
        self.main_box.add(self.arrivals_label)
        self.add(self.main_box)

        getRoutes()
    
    def on_route_selected(self, combo):
        self.stop_dropdown.remove_all()
        self.stop_data = []

        index = combo.get_active()
        if index == -1:
            return
        
        self.selected_route = self.routes_data[index]
        route_number = self.selected_route["route"]

        print(f"selected route: {route_number}")
        
        for direction in self.selected_route["dir"]:
            direction_name = direction["desc"]

            for stop in direction["stop"]:
                stop_text = f"{direction_name} - {stop['desc']}"
                self.stop_dropdown.append_text(stop_text)
                self.stop_data.append(stop)

    def on_stop_selected(self, combo):
        index = combo.get_active()
        if index == -1:
            return
        
        selected_stop = self.stop_data[index]
        locid = selected_stop["locid"]
        print(f"selected stop locid: {locid}")

        self.arrivalsUrl = f"https://developer.trimet.org/ws/v2/arrivals?appID={appID}&LocIDs={locid}&json=true"
        self.arrivalsResponse = requests.get(self.arrivalsUrl).json()

        arrivals = self.arrivalsResponse["resultSet"]["arrival"]
        self.arrival_info = ""

        for arrival in arrivals:
            route = arrival["route"]
            short_sign = arrival["shortSign"]

            current_time = self.arrivalsResponse["resultSet"]["queryTime"]
            if arrival.get("status") == "estimated" and "estimated" in arrival:
                arrival_time = arrival["estimated"]
            else:
                arrival_time = arrival["scheduled"]
            minutes = (arrival_time - current_time) // (1000 * 60)

            load_percent = arrival["loadPercentage"]

            arrival_info = f"{short_sign} - {minutes} min {load_percent}% full"
            print(arrival_info)

            self.arrival_info += arrival_info + "\n"
        
        self.arrivals_label.set_text(self.arrival_info)

win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()