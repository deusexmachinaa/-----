import re
import os
from datetime import datetime

# 로그 파일 경로 입력받기
def get_valid_log_file_path():
    while True:
        # 사용자로부터 로그 파일 경로 입력받기
        log_file_path = input("Enter the path to the log file or file name: ")
        
        # 입력받은 경로가 실제로 존재하는 파일인지 검사
        if os.path.isfile(log_file_path):
            return log_file_path
        else:
            print("The file does not exist. Please check the path and try again.")

log_file_path = get_valid_log_file_path()

# 파일 이름과 확장자 분리
log_file_name, _ = os.path.splitext(os.path.basename(log_file_path))

# 현재 시간을 기반으로 새 파일 이름 생성
current_time = datetime.now().strftime("%y%m%d%H%M")
result_file_name = f"{log_file_name}_Inspection_{current_time}.txt"
# 결과 파일 경로 설정 (동일 디렉토리에 저장)
result_file_path = os.path.join(os.path.dirname(log_file_path), result_file_name)
print(f"Analyzing logs from {log_file_path}...")

# 타임스탬프 추출 함수
def parse_timestamp(line):
    match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', line)
    return datetime.strptime(match.group(), '%Y-%m-%d %H:%M:%S.%f') if match else None

# 로그 분석 함수
def analyze_logs(file_path):
    heartbit_times = []
    cells_started = set()
    cells_completed = set()
    cells_with_image_saved = set()  # 추가
    grab_flag_on = False
    grab_flag_times = []

    with open(file_path, 'r', encoding='utf-8') as file, open(result_file_path , 'w', encoding='utf-8') as output_file:
        for line in file:
            timestamp = parse_timestamp(line)
            
            if 'HeartBit' in line:
                heartbit_times.append(timestamp)
            elif '[GRAB]' in line:
                cell_id = re.search(r'CellId (\S+)', line)
                if cell_id:
                    cells_started.add(cell_id.group(1))
            elif 'MES Report Done' in line:
                cell_id = re.search(r'Cell ID : \[ (\S+) \]', line)
                if cell_id:
                    cells_completed.add(cell_id.group(1))
            elif 'Raw Image Save' in line:
                cell_id = cell_id = re.search(r'\d{14}_(\w+)_\d+x\d+', line)  # 필요에 따라 정규 표현식 수정 필요
                if cell_id:
                    cells_with_image_saved.add(cell_id.group(1))
            elif 'Grab Flag is still now on' in line:
                grab_flag_on = True
                grab_flag_times.append(timestamp)
    
        # HeartBit 간격 분석
        for i in range(1, len(heartbit_times)):
            interval = heartbit_times[i] - heartbit_times[i-1]
            interval_seconds = interval.total_seconds()
            if (heartbit_times[i] - heartbit_times[i-1]).total_seconds() > 3:
                interval_rounded = round(interval_seconds, 3)
                print(f"HeartBit interval > 3s between {heartbit_times[i-1]} and {heartbit_times[i]} => {interval_rounded}s")
                output_file.write(f"HeartBit interval > 3s between {heartbit_times[i-1]} and {heartbit_times[i]} => {interval_rounded}s\n")
        
        # MES Report Done이 없는 Cell ID 출력
        cells_not_reported = cells_started - cells_completed
        if cells_not_reported:
            print(f"Cells not reported: {cells_not_reported} , {len(cells_not_reported)} cells")
            output_file.write(f"Cells not reported: {cells_not_reported} , {len(cells_not_reported)} cells\n")
        else:
            print("All started cells have been reported.")
            output_file.write("All started cells have been reported.\n")
        
        # Raw Image Save가 없는 Cell ID 출력
        cells_without_images = cells_started - cells_with_image_saved
        if cells_without_images:
            print(f"Cells with no raw images saved: {cells_without_images} , {len(cells_without_images)} cells")
            output_file.write(f"Cells with no raw images saved: {cells_without_images} , {len(cells_without_images)} cells\n")
        else:
            print("Raw images saved for all started cells.")
            output_file.write("Raw images saved for all started cells.\n")
        
        # Grab Flag On 여부 출력
        if grab_flag_on:
            print("'Grab Flag is still now on' found in the log.")
            output_file.write("'Grab Flag is still now on' found in the log.\n")
        else:
            print("No 'Grab Flag is still now on' found in the log.")
            output_file.write("'No Grab Flag is still now on' found in the log.\n")

def main():
    analyze_logs(log_file_path)

if __name__ == "__main__":
    main()
    print(f"Analysis complete. Results saved to {result_file_path}")
    input("Press Enter to exit...")