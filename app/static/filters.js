/**
 * Funções de filtro centralizadas para todos os templates
 */

/**
 * Filtra players na listagem por nome e guilda
 * Inclui suporte a ambos os campos ou apenas um
 */
function filterPlayers() {
    const search = document.getElementById('search');
    const guildFilter = document.getElementById('guildFilter');
    
    const keyword = search ? search.value.toLowerCase() : '';
    const guildKeyword = guildFilter ? guildFilter.value : '';
    
    const players = document.querySelectorAll('.player-item');
    
    players.forEach(player => {
        const name = player.querySelector('.player-name').textContent.toLowerCase();
        const guildElement = player.querySelector('.player-guild');
        const guild = guildElement ? guildElement.textContent : '';
        
        const nameMatch = !keyword || name.includes(keyword);
        const guildMatch = !guildKeyword || guild.includes(guildKeyword);
        
        player.style.display = (nameMatch && guildMatch) ? 'grid' : 'none';
    });
}

/**
 * Filtra players apenas por nome (para páginas que não têm filtro de guilda)
 */
function filterPlayersByName() {
    const search = document.getElementById('search');
    const keyword = search ? search.value.toLowerCase() : '';
    
    const players = document.querySelectorAll('.player-item');
    
    players.forEach(player => {
        const name = player.querySelector('.player-name').textContent.toLowerCase();
        player.style.display = keyword && name.includes(keyword) || !keyword ? 'grid' : 'none';
    });
}

/**
 * Suporta busca em tempo real em formulários
 */
function setupLiveSearch(searchInputId, resultsContainerId, searchFunction) {
    const searchInput = document.getElementById(searchInputId);
    const resultsContainer = document.getElementById(resultsContainerId);
    
    if (!searchInput || !resultsContainer) return;
    
    searchInput.addEventListener('input', function() {
        const keyword = this.value.toLowerCase();
        
        if (!keyword) {
            resultsContainer.innerHTML = '';
            return;
        }
        
        if (typeof searchFunction === 'function') {
            searchFunction(keyword, resultsContainer);
        }
    });
}
