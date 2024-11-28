from flask import Flask, request, jsonify
import os
from queue_manager import check_queue_status
from printer_manager import get_printer_status, update_print_status
from local_database import New_print

app = Flask(__name__)
