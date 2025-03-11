import csv
import random
import time
from datetime import datetime

# Define the CSV file name
csv_file = 'updated_data_net.csv'

# Function to generate random data
def generate_random_data(no):
    time_value = round(random.uniform(0, 100), 1)  # Random time value
    source = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"  # Random IP
    destination = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"  # Random IP
    protocol = random.choice(['TCP', 'UDP', 'NAT'])  # Random protocol
    length = random.randint(13000, 20000)  # Random length
    info = random.choice(['real-time', 'delayed', 'unknown'])  # Random info

    return [no, time_value, source, destination, protocol, length, info]

# Function to get the next row number
def get_next_row_number(file_name):
    try:
        with open(file_name, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if len(rows) > 1:  # Check if there are data rows
                last_row = rows[-1]
                return int(last_row[0]) + 1  # Increment last row number
            else:
                return 1  # Start from 1 if file is empty
    except FileNotFoundError:
        return 1  # Start from 1 if the file does not exist

# Get the next row number
no = get_next_row_number(csv_file)

# Main loop to write random data every minute
while True:
    # Generate random data
    data = generate_random_data(no)
    
    # Append data to the CSV file
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write header if the file is empty
        if file.tell() == 0:
            writer.writerow(['No.', 'Time', 'Source', 'Destination', 'Protocol', 'Length', 'Info'])
        
        writer.writerow(data)
    
    print(f'Added data: {data}')
    
    # Increment the row number
    no += 1
    
    # Wait for 10 seconds
    time.sleep(10)