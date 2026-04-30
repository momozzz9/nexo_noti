import scheduler
import datetime

def main():
    print("=" * 50)
    print("Starting Economic Newsletter Dispatch")
    print(f"   Execution Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # 스케줄러의 즉시 실행 함수 호출
        scheduler.run_immediate()
        print("\n[SUCCESS] Newsletter sent to all subscribers!")
    except Exception as e:
        print(f"\n[ERROR] Failed to send newsletter: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
