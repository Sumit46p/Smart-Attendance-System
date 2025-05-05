import pandas as pd
import os
from datetime import datetime

def mark_attendance(student_name, folder_path='attendance_records'):
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    file_path = os.path.join(folder_path, f'attendance_{date_str}.csv')

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['Student Name', 'Date', 'Time', 'Status'])
    else:
        df = pd.read_csv(file_path)

    # Avoid duplicate entry
    if student_name in df['Student Name'].values:
        print(f"{student_name} is already marked present.")
    else:
        new_row = {'Student Name': student_name, 'Date': date_str, 'Time': time_str, 'Status': 'Present'}
        df = df.append(new_row, ignore_index=True)
        df.to_csv(file_path, index=False)
        print(f"{student_name} marked as Present.")
