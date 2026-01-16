document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');

    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim();

        // Если поле пустое — чистим всё и прячем блок
        if (query.length === 0) {
            resultsContainer.innerHTML = '';
            resultsContainer.classList.add('hidden'); // Добавляем класс скрытия
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${query}`);
            if (!response.ok) throw new Error('Network error');
            const lectures = await response.json();

            // Показываем блок, так как пошли результаты
            resultsContainer.classList.remove('hidden');
            renderResults(lectures);
        } catch (error) {
            console.error(error);
        }
    });

    function renderResults(lectures) {
        resultsContainer.innerHTML = '';

        if (lectures.length === 0) {
            resultsContainer.innerHTML = `
                <div class="p-6 text-center text-gray-500 font-mono text-sm">
                    Ничего не найдено
                </div>
            `;
            return;
        }

        lectures.forEach(lecture => {
            const div = document.createElement('div');
            // Стили те же
            div.className = 'p-4 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors flex justify-between items-center group';

            div.innerHTML = `
                <div>
                    <h4 class="font-display font-bold text-sm text-white group-hover:text-omiRed transition-colors">${lecture.title}</h4>
                    <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-1">${lecture.subject} • ${lecture.author}</p>
                </div>
                <svg class="w-4 h-4 text-gray-600 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
            `;

            // ВОТ ГЛАВНОЕ ИЗМЕНЕНИЕ: ПЕРЕХОД ПО ID
            div.addEventListener('click', () => {
                window.location.href = `/lecture/${lecture.id}`;
            });

            resultsContainer.appendChild(div);
        });
    }
    document.addEventListener('click', (e) => {
    // Если клик не по инпуту и не по результатам — закрываем список
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.innerHTML = '';
            resultsContainer.classList.add('hidden');
        }
    });
});

