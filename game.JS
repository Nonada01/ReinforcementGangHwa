// --- 기본 설정 ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const missesEl = document.getElementById('misses');
const startButton = document.getElementById('startButton');

const BROWN = '#8B4513'; // 두더지 색
const HOLE_COLOR = '#5C3317'; // 구멍 색

// 파이썬 환경과 동일한 구멍 위치 설정
const holePositions = [];
for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
        holePositions.push({ x: 160 + c * 200, y: 150 + r * 150 });
    }
}

// --- 게임 상태 변수 ---
let score = 0;
let missedMoles = 0;
let moles = [
    { isUp: false, timer: 0, hideTime: 60, pos: null, posIndex: -1 },
    { isUp: false, timer: 0, hideTime: 60, pos: null, posIndex: -1 },
    { isUp: false, timer: 0, hideTime: 60, pos: null, posIndex: -1 }
];
let moleSpawnTimer = 0;
let ortSession;
let gameRunning = false;


// --- 그리기 함수 ---
function drawHoles() {
    ctx.fillStyle = HOLE_COLOR;
    holePositions.forEach(pos => {
        ctx.beginPath();
        ctx.ellipse(pos.x, pos.y + 30, 60, 20, 0, 0, 2 * Math.PI);
        ctx.fill();
    });
}

function drawMoles() {
    ctx.fillStyle = BROWN;
    moles.forEach(mole => {
        if (mole.isUp) {
            const upAmount = Math.min(1, mole.timer / 10) * 80;
            ctx.beginPath();
            // 타원형 몸체
            ctx.ellipse(mole.pos.x, mole.pos.y - upAmount / 2 + 30, 50, 40, 0, 0, 2 * Math.PI);
            ctx.fill();
        }
    });
}

function drawUI() {
    scoreEl.textContent = score;
    missesEl.textContent = missedMoles;
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// --- 게임 로직 함수 ---
function resetGame() {
    score = 0;
    missedMoles = 0;
    moles.forEach(m => {
        m.isUp = false;
        m.pos = null;
        m.posIndex = -1;
    });
    moleSpawnTimer = 0;
    drawUI();
}

async function runAI() {
    if (!gameRunning) return;

    // 1. 관찰 데이터 생성 (Python의 _get_obs()와 동일)
    const observation = new Float32Array(9).fill(0.0);
    moles.forEach(mole => {
        if (mole.isUp) {
            const remainingTime = (mole.hideTime - mole.timer) / mole.hideTime;
            observation[mole.posIndex] = Math.max(0.0, remainingTime);
        }
    });

    // 2. ONNX 모델에 입력
    const inputs = { 'observation': new ort.Tensor('float32', observation, [1, 9]) };
    const results = await ortSession.run(inputs);
    const actionLogits = results.action.data; // 모델의 출력값 (각 행동에 대한 점수)

    // 3. 가장 높은 점수의 행동 선택 (ArgMax)
    const action = actionLogits.indexOf(Math.max(...actionLogits));

    // 4. 행동 실행 (Python의 step() 로직 모방)
    if (action > 0) {
        const hitPosIndex = action - 1;
        let hitSuccess = false;
        moles.forEach(mole => {
            if (mole.isUp && mole.posIndex === hitPosIndex) {
                mole.isUp = false;
                score++;
                hitSuccess = true;
            }
        });
    }

    // 두더지 상태 업데이트 및 생성
    moleSpawnTimer++;
    const spawnRate = Math.max(15, 60 - score);
    if (moleSpawnTimer > spawnRate) {
        moleSpawnTimer = 0;
        const inactiveMoles = moles.filter(m => !m.isUp);
        
        const occupiedHoleIndices = moles.filter(m => m.isUp).map(m => m.posIndex);
        const availableHoleIndices = [0,1,2,3,4,5,6,7,8].filter(i => !occupiedHoleIndices.includes(i));
        
        if (inactiveMoles.length > 0 && availableHoleIndices.length > 0) {
            const moleToPop = inactiveMoles[0];
            const holeIndex = availableHoleIndices[Math.floor(Math.random() * availableHoleIndices.length)];
            
            moleToPop.isUp = true;
            moleToPop.pos = holePositions[holeIndex];
            moleToPop.posIndex = holeIndex;
            moleToPop.hideTime = Math.max(20, 60 - Math.floor(score / 5));
            moleToPop.timer = 0;
        }
    }

    moles.forEach(mole => {
        if (mole.isUp) {
            mole.timer++;
            if (mole.timer > mole.hideTime) {
                mole.isUp = false;
                missedMoles++;
            }
        }
    });

    // 게임 종료 조건
    if (missedMoles >= 10) {
        alert(`게임 오버! 최종 점수: ${score}`);
        gameRunning = false;
        startButton.disabled = false;
        startButton.textContent = "AI 다시 시작";
        return;
    }

    // 화면 다시 그리기
    clearCanvas();
    drawHoles();
    drawMoles();
    drawUI();

    // 다음 프레임 요청
    requestAnimationFrame(runAI);
}

// --- 초기화 및 이벤트 리스너 ---
startButton.addEventListener('click', async () => {
    if (!ortSession) {
        try {
            // ONNX 모델 로드
            ortSession = await ort.InferenceSession.create('./whac-a-mole.onnx');
            console.log("ONNX 모델 로드 성공!");
        } catch (e) {
            console.error("ONNX 모델 로드 실패:", e);
            alert("AI 모델을 불러오는 데 실패했습니다. 콘솔을 확인해주세요.");
            return;
        }
    }

    resetGame();
    gameRunning = true;
    startButton.disabled = true;
    startButton.textContent = "AI 실행 중...";
    runAI(); // AI 게임 루프 시작
});

// 초기 화면 그리기
drawHoles();