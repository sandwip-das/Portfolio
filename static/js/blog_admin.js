document.addEventListener('DOMContentLoaded', function () {
    // Analytics Inline IDs (related names from models)
    const inlines = [
        { id: 'view_tracks', title: 'View Tracks' },
        { id: 'reactions', title: 'Reactions' },
        { id: 'comments', title: 'Comments' }
    ];

    inlines.forEach(inline => {
        const group = document.getElementById(inline.id + '-group');
        if (group) {
            // Add custom header/toggle
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'inline-summary-wrapper';
            summaryDiv.style.cssText = `
                background: var(--darkened-bg, rgba(0,0,0,0.03)); 
                border: 1px solid var(--border-color, #dee2e6); 
                border-radius: 4px; 
                padding: 12px 18px; 
                margin-bottom: 20px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                cursor: pointer;
                transition: background 0.2s;
            `;

            const rows = group.querySelectorAll('tr.has_original, tr.dynamic-view_tracks, tr.dynamic-reactions, tr.dynamic-comments');
            const count = rows.length;

            summaryDiv.innerHTML = `
                <div style="font-weight: 600; color: var(--body-fg, #444); font-size: 14px;">
                    <i class="fas fa-chart-line" style="margin-right: 8px; color: var(--link-fg, #3498db);"></i>
                    ${inline.title} 
                    <span style="font-weight: 400; color: var(--body-quiet-fg, #888); margin-left:12px; font-size: 13px;">(${count} recorded)</span>
                </div>
                <div class="expand-btn" style="color: var(--link-fg, #3498db); font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                    <i class="fas fa-plus-circle" style="margin-right: 4px;"></i> Expand
                </div>
            `;

            group.style.display = 'none';
            group.parentNode.insertBefore(summaryDiv, group);

            summaryDiv.addEventListener('click', function () {
                if (group.style.display === 'none') {
                    group.style.display = 'block';
                    this.querySelector('.expand-btn').innerHTML = '<i class="fas fa-minus-circle" style="margin-right: 4px;"></i> Collapse';
                    this.style.background = 'var(--selected-bg, rgba(0,0,0,0.08))';
                } else {
                    group.style.display = 'none';
                    this.querySelector('.expand-btn').innerHTML = '<i class="fas fa-plus-circle" style="margin-right: 4px;"></i> Expand';
                    this.style.background = 'var(--darkened-bg, rgba(0,0,0,0.03))';
                }
            });
        }
    });
});
