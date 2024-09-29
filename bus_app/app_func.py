#!/usr/bin/env python3
import os
import csv
import requests
from telegram import Update
from app_utils import *
from text_utils import *
from llm import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from asyncio import get_running_loop


class App:
    _bus_arrival = {
        "199": {
            "bus_stop_0": {
                "est_arrival_1": "0",  # wall time
                "est_arrival_2": "0",  # wall time
            }
        }
    }

    # Constructor
    def __init__(
        self,
        lta_api_key: str = "",
        bus_stop_code: str = "",
        bus_service_no: str = "",
        groq_api_key: str = "",
    ):
        # Function_map
        self._param_map = {
            "BUS_ARRIVAL": {
                "description": "Get the bus arrival time. Activate if user asks questions such as: when is the bus coming?\
                    Only fill in <bus_service_no> if the user mentions about the specific bus service number. Only fill in <bus_stop_code>\
                    if the user mentions about the specific bus stop code. If user asks question like: when is 199 coming? You should know \
                    that 199 refers to the bus service number, so you should return BUS_ARRIVAL<199>. If the user asks question like: when \
                    is 199 arriving at 22009, you should return BUS_ARRIVAL<199><22009>.",
                "request_retry": 3,
                "bus_service_no": bus_service_no,
                "bus_stop_code": bus_stop_code,
                "reminder_mins": [15.0],  # in mins
                "function_architype": "BUS_ARRIVAL<bus_service_no><bus_stop_code>",
                "function": self.bus_arrival_async,
            },
            "GET_BUS_SERVICE_NUMBER": {
                "description": "Get the bus service number that you are currently tracking.",
                "function_architype": "GET_BUS_SERVICE_NUMBER",
                "function": self.get_bus_service_no_async,
            },
            "GET_BUS_STOP_CODE": {
                "description": "Get the bus stop code that you are currently tracking.",
                "function_architype": "GET_BUS_STOP_CODE",
                "function": self.get_bus_stop_code_async,
            },
            "GET_REMINDER": {
                "description": "Get the reminder time before the bus arrives that was already set.",
                "function_architype": "GET_REMINDER",
                "function": self.get_reminder_async,
            },
            "SET_REMINDER": {
                "description": "Set the reminder time in minutes before the bus arrives.",
                "function_architype": "SET_REMINDER<mins_before_bus_arrives><false>",
                "function": self.set_reminder_async,
            },
            "SET_ONLY_ONE_REMINDER": {
                "description": "Set only one reminder time in minutes before the bus arrives.",
                "function_architype": "SET_REMINDER<mins_before_bus_arrives><true>",
                "function": self.set_reminder_async,
            },
            "SET_BUS_SERVICE_NO": {
                "description": "Set the bus service number to be kept tracked of its arrival time.",
                "function_architype": "SET_BUS_SERVICE_NO<bus_service_no>",
                "function": self.set_bus_service_no_async,
            },
            "SET_BUS_STOP_CODE_FROM_CODE": {
                "description": "Set the bus stop code to be kept tracked of the bus arrival time, given bus stop code.",
                "function_architype": "SET_BUS_STOP_CODE_FROM_CODE<bus_stop_code><false>",
                "function": self.set_bus_stop_code_async,
            },
            "SET_BUS_STOP_CODE_FROM_NAME": {
                "description": "Set the bus stop code to be kept tracked of the bus arrival time, given bus stop name.",
                "function_architype": "SET_BUS_STOP_CODE_FROM_NAME<bus_stop_name><true>",
                "function": self.set_bus_stop_code_async,
            },
            "GET_BUS_STOP_NAME_FROM_CODE": {
                "description": "Get the given bus stop code and convert it to bus stop name. Trigger when user asks questions like: What is the bus stop name of XXX (bus stop code). \
                    If the user mentions about Boon Lay, it is most likely refering to bus stop name Jurong West Ctrl 3-Boon Lay Int",
                "function_architype": "GET_BUS_STOP_NAME_FROM_CODE<bus_stop_code>",
                "function": self.bus_stop_code_to_name_async,
            },
            "GET_BUS_STOP_CODE_FROM_NAME": {
                "description": "Get the given bbus stop name and convert it to bus stop code. Trigger when user asks questions like: What is the bus stop code of XXX (bus stop name).",
                "function_architype": "GET_BUS_STOP_CODE_FROM_NAME<bus_stop_name>",
                "function": self.bus_stop_name_to_code_async,
            },
            "SHOW_BUS_ROUTE": {
                "description": "Show the bus route. Trigger when user asks questions like: show me the bus route.",
                "function_architype": "SHOW_BUS_ROUTE<bus_service_number>",
                "function": self.send_bus_stop_image_async,
            },
            
        }

        self._lta_api_key = lta_api_key

        # LLM
        self._llm = LLM(api_key=groq_api_key, param_map=self._param_map)

        # Scheduler
        self._scheduler = AsyncIOScheduler()
        self._scheduler.start()

    # Destructorr
    def __del__(self):
        pass

    # ======================================== Get & Set Attributes ========================================
    ## Set
    def set_bus_service_no(self, bus_service_no: str, *args, **kwargs):
        self._param_map["BUS_ARRIVAL"]["bus_service_no"] = str(bus_service_no)

    def set_bus_stop_code(self, bus_stop_code: str, *args, **kwargs):
        self._param_map["BUS_ARRIVAL"]["bus_stop_code"] = str(bus_stop_code)

    def set_reminder(
        self, min_before_arrival: float, remove_other: bool = False, *args, **kwargs
    ):
        if remove_other:
            self.clear_reminder()
        if min_before_arrival not in self._param_map["BUS_ARRIVAL"]["reminder_mins"]:
            self._param_map["BUS_ARRIVAL"]["reminder_mins"].append(min_before_arrival)

    def remove_reminder(self, min_before_arrival: float, *args, **kwargs):
        self._param_map["BUS_ARRIVAL"]["reminder_mins"].remove(min_before_arrival)

    def clear_reminder(self, *args, **kwargs):
        self._param_map["BUS_ARRIVAL"]["reminder_mins"].clear()

    def reset(self, *args, **kwargs):
        self.clear_reminder()
        
    ## Get
    def get_bus_service_no(self, *args, **kwargs):
        return self._param_map["BUS_ARRIVAL"]["bus_service_no"]

    def get_bus_stop_code(self, *args, **kwargs):
        return self._param_map["BUS_ARRIVAL"]["bus_stop_code"]

    def get_reminder(self, *args, **kwargs):
        return self._param_map["BUS_ARRIVAL"]["reminder_mins"]

    def bus_stop_code_to_name(self, bus_stop_code: str, *args, **kwargs):
        print("-"*10)
        print(f"[{get_time_now()}] Received bus stop name request.")
        file_path = os.path.dirname(__file__) + "/../data/bus_stop.csv"
        if os.path.exists(file_path):
            bus_stop_dict = bus_stop_raw_to_dict(file_path)
            return (
                bus_stop_dict[bus_stop_code] if bus_stop_code in bus_stop_dict else None
            )
        return None

    def bus_stop_name_to_code(
        self, bus_stop_name: str, bus_service_no: str = None, *args, **kwargs
    ):
        if bus_service_no is None:
            bus_service_no = self.get_bus_service_no()

        file_path = os.path.dirname(__file__) + f"/../data/{bus_service_no}_route.csv"
        if os.path.exists(file_path):
            bus_stop_dict = csv_to_dict(file_path)
            llm_reply = self._llm.prompt(
                f"Given this map of bus stop code and bus stop name: {str(bus_stop_dict)}, Only return the exact bus stop code which has \
                    the name that is the most similar to the requested: {bus_stop_name}."
            )
            print(f"[{get_time_now()}] [bus_stop_name_to_code] LLM reply: {llm_reply}")
            func_name, args = extract_function_info(llm_reply)
            if args is not None and len(args) > 0:
                return args[0]
            return llm_reply
        else:
            return None

    # ======================================== App's Functions ========================================
    def get_bus_arrival_info(self):
        param = self._param_map["BUS_ARRIVAL"]
        retry = param["request_retry"]
        BUS_SERVICE_NO = param["bus_service_no"]
        BUS_STOP_CODE = param["bus_stop_code"]
        LTA_API_KEY = self._lta_api_key

        url = f"https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode={BUS_STOP_CODE}&ServiceNo={BUS_SERVICE_NO}"
        payload = {}
        headers = {"AccountKey": LTA_API_KEY, "accept": "application/json"}

        response = None
        for _ in range(retry):
            if response is not None:
                break
            try:
                response = requests.request("GET", url, headers=headers, data=payload)
            except:
                response = None
                continue
        if response is None:
            return "No bus services found."
        data = response.json()

        if "Services" in data.keys() and len(data["Services"]) > 0:
            service = data["Services"][0]
            next_bus = service["NextBus"]["EstimatedArrival"]
            next_bus_2 = service["NextBus2"]["EstimatedArrival"]

            if (BUS_SERVICE_NO not in self._bus_arrival) or (
                BUS_SERVICE_NO in self._bus_arrival
                and BUS_STOP_CODE not in self._bus_arrival[BUS_SERVICE_NO]
            ):
                new_map = {
                    BUS_SERVICE_NO: {
                        BUS_STOP_CODE: {
                            "est_arrival_1": "0",
                            "est_arrival_2": "0",
                        }
                    }
                }
                self._bus_arrival.update(new_map)

            self._bus_arrival[BUS_SERVICE_NO][BUS_STOP_CODE]["est_arrival_1"] = (
                process_time(next_bus, include_date=True)
            )
            self._bus_arrival[BUS_SERVICE_NO][BUS_STOP_CODE]["est_arrival_2"] = (
                process_time(next_bus_2, include_date=True)
            )

            # Reply text
            return f"Next bus {BUS_SERVICE_NO} arriving at station {BUS_STOP_CODE} at {process_time(next_bus)}, followed by {process_time(next_bus_2)}"
        else:
            return "No bus services found."

    def get_bus_stop_info(self, recreate: bool = False):
        file_path = os.path.dirname(__file__) + "/../data/bus_stop.csv"
        if os.path.exists(file_path) and not recreate:
            return "Bus stop information is already fetched."
        else:
            LTA_API_KEY = self._lta_api_key

            url = "https://datamall2.mytransport.sg/ltaodataservice/BusStops"
            payload = {}
            headers = {"AccountKey": LTA_API_KEY, "accept": "application/json"}

            bus_stops = []
            skip = 0
            while True:
                # Modify URL to include $skip for pagination
                paginated_url = f"{url}?$skip={skip}"
                response = requests.get(paginated_url, headers=headers)

                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    break

                data = response.json()

                # Check if the response contains results
                if "value" in data and data["value"]:
                    bus_stops.extend(data["value"])

                    # If we got fewer than 500 records, we've reached the end of the dataset
                    if len(data["value"]) < 500:
                        break
                    # Otherwise, continue to the next page by incrementing the skip value
                    skip += 500
                else:
                    # No more data
                    break

            with open(file_path, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=bus_stops[0].keys())
                writer.writeheader()
                writer.writerows(bus_stops)

            return "Created bus_stop.csv"

    # ======================================== App's Async Functions ========================================
    async def start(self, update: Update, context):
        await asyncio.sleep(0.2)
        await update.message.reply_text(self._llm.prompt("Hi, tell me who you are."))

    async def send_reminder(self, update: Update, mins_left, bus_service_no, bus_stop_code, args_list: list = []):
        print(f"[{get_time_now()}] Sending reminder.")
        await asyncio.sleep(0.2)
        await update.message.reply_text(
            f"The bus {bus_service_no} is arriving at {bus_stop_code} in <b>{str(mins_left)} min </b>! Get Ready soon!",
            parse_mode="HTML",
        )

    async def bus_arrival_async(self, update: Update, context, args_list: list = []):
        print("-"*10)
        print(f"[{get_time_now()}] Received bus arrival request.")

        if len(args_list) > 0 and args_list[0].isdigit():
            self.set_bus_service_no(args_list[0])
        if len(args_list) > 1:
            if args_list[1].isdigit():
                self.set_bus_stop_code(args_list[1])
            else:
                code = self.bus_stop_name_to_code(args_list[1])
                if code is not None:
                    self.set_bus_stop_code(code)

        bus_info = self.get_bus_arrival_info()
        print(f"[{get_time_now()}] {bus_info}")

        await asyncio.sleep(0.2)
        await update.message.reply_text(bus_info)

        # Set reminder
        if len(self._param_map["BUS_ARRIVAL"]["reminder_mins"]) > 0:
            # Data Processing
            reminder_min = sorted(
                self._param_map["BUS_ARRIVAL"]["reminder_mins"], reverse=True
            )
            bus_has_passed = True
            bus_service_no = self._param_map["BUS_ARRIVAL"]["bus_service_no"]
            bus_stop_code = self._param_map["BUS_ARRIVAL"]["bus_stop_code"]

            # Add reminder task
            for key in ["est_arrival_1", "est_arrival_2"]:
                for each in reminder_min:
                    remind_time = self._bus_arrival[bus_service_no][bus_stop_code][
                        key
                    ].replace(tzinfo=None) - timedelta(minutes=each)

                    if remind_time < get_datetime_now():
                        continue

                    bus_has_passed = False
                    current_loop = get_running_loop()

                    self._scheduler.add_job(
                        lambda each=each: asyncio.run_coroutine_threadsafe(
                            self.send_reminder(
                                update,
                                mins_left=each,
                                bus_service_no = bus_service_no,
                                bus_stop_code = bus_stop_code
                            ),
                            current_loop,
                        ),
                        "date",
                        run_date=remind_time,
                    )
                    await asyncio.sleep(0.2)
                    await update.message.reply_text(
                        f"You will receive a reminder at {remind_time}"
                    )

                if bus_has_passed and key == "est_arrival_1":
                    await asyncio.sleep(0.2)
                    await update.message.reply_text(
                        "The 1st bus has already passed. Setting reminder for the 2nd bus."
                    )
                else:
                    break

            if bus_has_passed:
                await asyncio.sleep(0.2)
                await update.message.reply_text(
                    "I'm sorry. I can't set the requested reminder. Please reduce the reminder time or try again later."
                )

    async def bus_stop_async(self, update: Update, context, args_list: list = []):
        print("-"*10)
        print(f"[{get_time_now()}] Received bus stop info request.")
        bus_stop_info = self.get_bus_stop_info()
        print(f"[{get_time_now()}] {bus_stop_info}")
        await asyncio.sleep(0.2)
        await update.message.reply_text(bus_stop_info)

    async def get_bus_service_no_async(
        self, update: Update, context, args_list: list = []
    ):
        print("-"*10)
        print(f"[{get_time_now()}] Received get bus service number request.")
        bus_service_no = self.get_bus_service_no()
        print(f"[{get_time_now()}] {bus_service_no}")
        
        await asyncio.sleep(0.2)
        await update.message.reply_text(f"Current bus service no.: {bus_service_no}")

    async def get_bus_stop_code_async(
        self, update: Update, context, args_list: list = []
    ):
        print("-"*10)
        print(f"[{get_time_now()}] Received get bus stop code request.")
        bus_stop_code = self.get_bus_stop_code()
        print(f"[{get_time_now()}] {bus_stop_code}")
        
        await asyncio.sleep(0.2)
        await update.message.reply_text(f"Current bus stop code: {bus_stop_code}")

    async def get_reminder_async(self, update: Update, context, args_list: list = []):
        print("-"*10)
        print(f"[{get_time_now()}] Received get reminder request.")
        reminder_list = self.get_reminder()
        print(f"[{get_time_now()}] {str(reminder_list)}")
        llm_reply = self._llm.prompt(
            f"Don't output the function architype this time but output an improved sentence of this: Reminder will be sent \
                x mins before the bus arrives upon the next bus arrival request, where x is {str(reminder_list)}"
        )
        
        await asyncio.sleep(0.2)
        await update.message.reply_text(llm_reply)

    async def set_bus_service_no_async(
        self, update: Update, context, args_list: list = []
    ):
        print("-"*10)
        print(f"[{get_time_now()}] Received set bus service no request.")
        bus_service_no = (
            args_list[0] if len(args_list) > 0 else self.get_bus_service_no()
        )
        self.set_bus_service_no(bus_service_no)
        print(f"[{get_time_now()}] Set bus service no: done")
        
        await asyncio.sleep(0.2)
        await update.message.reply_text(
            f"Bus service set to: {self.get_bus_service_no()}"
        )

    async def set_bus_stop_code_async(
        self, update: Update, context, args_list: list = []
    ):
        print("-"*10)
        print(f"[{get_time_now()}] Received set bus stop code request.")
        bus_stop_code = args_list[0] if len(args_list) > 0 else self.get_bus_stop_code()
        is_name = (args_list[1].lower() == "true") if len(args_list) > 1 else True
        if is_name:
            bus_stop_code = self.bus_stop_name_to_code(bus_stop_code)
        self.set_bus_stop_code(bus_stop_code)
        print(f"[{get_time_now()}] Set bus stop code: done")
        
        await asyncio.sleep(0.2)
        await update.message.reply_text(
            f"Bus stop code set to: {self.get_bus_stop_code()}"
        )

    async def bus_stop_code_to_name_async(
        self, update: Update, context, args_list: list = []
    ):
        bus_stop_code = args_list[0] if len(args_list) > 0 else self.get_bus_stop_code()
        print("-"*10)
        print(f"[{get_time_now()}] Received bus stop name request.")
        result = self.bus_stop_code_to_name(bus_stop_code)
        await asyncio.sleep(0.2)
        if result is not None:
            await update.message.reply_text(
                f"The name of bus stop {bus_stop_code} is {result}."
            )
        else:
            await update.message.reply_text(
                f"The name of bus stop {bus_stop_code} is not found."
            )

    async def bus_stop_name_to_code_async(
        self, update: Update, context, args_list: list = []
    ):
        bus_stop_name = args_list[0] if len(args_list) > 0 else ""
        print("-"*10)
        print(f"[{get_time_now()}] Received bus stop code request.")
        result = self.bus_stop_name_to_code(bus_stop_name)
        await asyncio.sleep(0.2)
        if result is not None:
            await update.message.reply_text(
                f"The code of bus stop {bus_stop_name} is {result}."
            )
        else:
            await update.message.reply_text(
                f"The code of bus stop {bus_stop_name} is not found."
            )

    async def set_reminder_async(self, update: Update, context, args_list: list = []):
        print("-"*10)
        print(f"[{get_time_now()}] Received set reminder request.")
        min_bef_arrval = float(args_list[0]) if len(args_list) > 0 else 2.0
        remove_other = (args_list[1].lower() == "true") if len(args_list) > 1 else True
        self.set_reminder(min_bef_arrval, remove_other)
        print(f"[{get_time_now()}] {min_bef_arrval} is added to the reminder list.")
        await self.get_reminder_async(update, context)

    async def handle_text(self, update: Update, context, args_list: list = []):
        print("-"*10)
        print(f"[{get_time_now()}] Received text request.")
        llm_reply = self._llm.prompt(f"{update.message.text}")
        print(f"[{get_time_now()}] LLM reply: {llm_reply}")
        func_name, args = extract_function_info(llm_reply)
        print(f"[{get_time_now()}] Extracted: {func_name} {args}")

        if func_name is not None and func_name in self._param_map.keys():
            await self._param_map[func_name.upper()]["function"](
                update, context, args_list=args
            )
        else:
            await update.message.reply_text(llm_reply)

    async def send_bus_stop_image_async(
        self, update: Update, context, args_list: list = []
    ):
        print("-"*10)
        print(f"[{get_time_now()}] Received send bus stop image request.")

        bus_service_no = self.get_bus_service_no()
        if len(args_list) > 0:
            bus_service_no = args_list[0]
        file_path = os.path.dirname(__file__) + f"/../data/{bus_service_no}_route.png"
        
        await update.message.reply_text(f"This is the bus route of bus {bus_service_no}")
        await update.message.reply_photo(photo=open(file_path, "rb"))


if __name__ == "__main__":
    print("Please don't run this scipt directly.")
