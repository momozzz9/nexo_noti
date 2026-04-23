/**
 * USB 3.2 Rev 1.1 Presentation Logic
 * Handles slide navigation, progress bar, and keyboard shortcuts.
 */

document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.slide');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const slideIndicator = document.getElementById('slideIndicator');
    const progressFill = document.getElementById('progressFill');

    let currentSlide = 0;
    const totalSlides = slides.length;

    /**
     * 슬라이드 업데이트 함수
     * @param {number} index - 보여줄 슬라이드 인덱스
     */
    function updateSlide(index) {
        // 모든 슬라이드 비활성화
        slides.forEach(slide => slide.classList.remove('active'));
        
        // 대상 슬라이드 활성화
        slides[index].classList.add('active');
        
        // 인디케이터 업데이트
        const displayIndex = (index + 1).toString().padStart(2, '0');
        const displayTotal = totalSlides.toString().padStart(2, '0');
        slideIndicator.textContent = `${displayIndex} / ${displayTotal}`;
        
        // 프로그레스 바 업데이트
        const progress = ((index + 1) / totalSlides) * 100;
        progressFill.style.width = `${progress}%`;
        
        // 버튼 상태 업데이트
        prevBtn.disabled = (index === 0);
        nextBtn.textContent = (index === totalSlides - 1) ? 'FINISH' : 'NEXT';
    }

    // 다음 슬라이드 이동
    nextBtn.addEventListener('click', () => {
        if (currentSlide < totalSlides - 1) {
            currentSlide++;
            updateSlide(currentSlide);
        } else {
            // 마지막 슬라이드에서 'FINISH' 클릭 시
            alert('강의 자료가 완료되었습니다. 삼성전자 HW 개발자 여러분의 성공적인 설계를 기원합니다!');
        }
    });

    // 이전 슬라이드 이동
    prevBtn.addEventListener('click', () => {
        if (currentSlide > 0) {
            currentSlide--;
            updateSlide(currentSlide);
        }
    });

    // 키보드 내비게이션 지원
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ') {
            nextBtn.click();
        } else if (e.key === 'ArrowLeft') {
            prevBtn.click();
        }
    });

    // 초기화
    updateSlide(currentSlide);
});
