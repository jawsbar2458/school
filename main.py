import cv2
import pyzbar.pyzbar as pyzbar
import gspread
from datetime import datetime, timedelta
from gtts import gTTS
from playsound import playsound

gc = gspread.service_account(filename='credentials.json')

id_sheet = gc.open_by_key("12jagC6TNQ0ge0950wLJf-BF_to4az6E44FrLnlHqb8g").worksheet("학생증 데이터")
record_sheet = gc.open_by_key("12jagC6TNQ0ge0950wLJf-BF_to4az6E44FrLnlHqb8g").worksheet("대여 현황")
log_sheet = gc.open_by_key("12jagC6TNQ0ge0950wLJf-BF_to4az6E44FrLnlHqb8g").worksheet("기록")

cap = cv2.VideoCapture(0) # 숫자 0은 메인카메라, 저 같은 경우는 노트북이니까 웹캠이 메인
last_data = ""
cnt = 0
doit = True

if not cap.isOpened():
    print("연결된 카메라 없음")
    exit()

def sound():
    playsound("play.mp3")

while True:
    success, frame = cap.read() # success는 카메라로 프레임 읽혔는지 확인하는 용도, false면 안읽힌거, frame은 현재 프레임(이미지)
    if success:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 녹화중인 카메라를 회색 계열로만 입력받는거
        decoded = pyzbar.decode(gray) #바코드 읽는거
    
        for d in decoded:
            #카메라에 실시간으로 표시하기 위해서 바코드 위치 가져오기
            x, y, w, h = d.rect
            #대충 학생증 바코드 밑에 그 숫자하고 영어 출력해주는거
            barcode_data = d.data.decode("utf-8")
            # type은 QR인지 바코드인지 구분하는건데 사실 학생증 바코드만 스캔하니까 필요는 없긴합니다
            barcode_type = d.type
            if doit == True:
                try:
                    tmp_data = id_sheet.row_values(id_sheet.find(barcode_data).row)
                    print(tmp_data)
                    cell = record_sheet.find(tmp_data[1]) # 학번
                    if cell == None:
                        return_date = datetime.today() + timedelta(3)
                        if return_date.isoweekday() == 6: # 토요일
                            return_date = return_date + timedelta(2)
                        elif return_date.isoweekday() == 7: #일요일
                            return_date = return_date + timedelta(1)
                        values = [tmp_data[0], tmp_data[1], datetime.today().strftime("%Y/%m/%d"), return_date.strftime("%Y/%m/%d")]
                        record_sheet.append_row(values)
                        log = [datetime.today().strftime("%Y/%m/%d"), datetime.today().strftime("%H:%M:%S"), f"{tmp_data[1]} {tmp_data[0]}", "대여"]
                        log_sheet.append_row(log)
                        # sound()
                        print(f"{tmp_data[0]} {tmp_data[1]} 등록 완료")
                        doit = False
                    else:
                        log = [datetime.today().strftime("%Y/%m/%d"), datetime.today().strftime("%H:%M:%S"), f"{tmp_data[1]} {tmp_data[0]}", "반납"]
                        log_sheet.append_row(log)
                        record_sheet.delete_rows(cell.row)
                        # sound()
                        print("반납 완료")
                        doit = False
                except:
                    print("기록 오류 발생")
            #여기부터는 그냥 카메라에 바코드 종류하고 바코드 밑에 숫자+영어 그거 표시해주는거
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            text = '%s (%s)' % (barcode_data, barcode_type)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
        if doit == False:
            cnt += 1
            if cnt == 50:
                doit = True
                cnt = 0
        cv2.imshow('webcam', frame) #웹캠 띄워주는 창
        key = cv2.waitKey(1) #1ms동안 키 입력 대기 / 값이 -1이면 1ms동안 아무 입력없었다는 뜻
        if key != -1: # -1 이 아니니까 키 입력했다는 뜻, 즉 프로그램 종료
            break
    else:
        print("카메라 녹화 에러")
        break

cap.release()
cv2.destroyAllWindows()
