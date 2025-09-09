// game.js 파일의 이 함수 전체를 교체하세요.
async function gameLoop() {
    if (!gameRunning) return;

    // 1. AI의 행동 결정
    const observation = new Float32Array(9).fill(0.0);
    moles.forEach(mole => {
        if (mole.isUp) {
            const remainingTime = (mole.hideTime - mole.timer) / mole.hideTime;
            observation[mole.posIndex] = Math.max(0.0, remainingTime);
        }
    });
    const inputs = { 'observation': new ort.Tensor('float32', observation, [1, 9]) };
    const results = await ortSession.run(inputs);
    
    // [수정 완료] BigInt 오류를 해결하는 핵심 코드입니다.
    const action = Number(results.action.data[0]);

    // 2. 결정된 행동 실행
    if (action > 0) {
        const hitPosIndex = action - 1;
        moles.forEach(mole => {
            if (mole.isUp && mole.posIndex === hitPosIndex) {
                mole.isUp = false;
                score++;
            }
        });
    }

    // 3. 게임 상태 업데이트 (두더지 생성/사라짐)
    updateGameState();

    // 4. 화면 그리기
    drawBackground();
    drawHoles();
    drawMoles();
    drawUI();

    // 5. 게임 종료 조건 확인
    if (missedMoles >= 10) {
        alert(`게임 오버! 최종 점수: ${score}`);
        gameRunning = false;
        startButton.disabled = false;
        startButton.textContent = "AI 다시 시작";
        return;
    }

    // 다음 프레임 요청
    requestAnimationFrame(gameLoop);
}