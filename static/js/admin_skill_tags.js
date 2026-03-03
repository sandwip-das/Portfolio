document.addEventListener('DOMContentLoaded', function () {
    function initSkillTags(textarea) {
        if (textarea.dataset.tagsInit) return;
        textarea.dataset.tagsInit = 'true';
        textarea.style.display = 'none';

        // Create Container
        const container = document.createElement('div');
        container.className = 'skill-tags-container';

        // Tag List Area
        const listDiv = document.createElement('div');
        listDiv.className = 'skill-tags-list';

        // Input Row
        const inputRow = document.createElement('div');
        inputRow.className = 'skill-input-row';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'skill-add-input';
        input.placeholder = 'Add new skill...';

        const btn = document.createElement('div');
        btn.className = 'skill-add-btn';
        btn.textContent = '+';
        btn.title = 'Add Skill';

        inputRow.appendChild(input);
        inputRow.appendChild(btn);
        container.appendChild(listDiv);
        container.appendChild(inputRow);

        textarea.parentNode.insertBefore(container, textarea);

        // Helper: Update Hidden Textarea
        function updateHidden() {
            const tags = Array.from(listDiv.querySelectorAll('.skill-tag span.text')).map(span => span.textContent);
            textarea.value = tags.join(', ');
        }

        // Helper: Add Tag to UI
        function addTag(text) {
            text = text.trim();
            if (!text) return;

            // Prevent duplicates (case-insensitive check?)
            const existing = Array.from(listDiv.querySelectorAll('.skill-tag span.text')).map(span => span.textContent.toLowerCase());
            if (existing.includes(text.toLowerCase())) return;

            const tag = document.createElement('span');
            tag.className = 'skill-tag';

            const txn = document.createElement('span');
            txn.className = 'text';
            txn.textContent = text;

            const remove = document.createElement('span');
            remove.className = 'remove-btn';
            remove.innerHTML = '&times;';
            remove.onclick = function () {
                tag.remove();
                updateHidden();
            };

            tag.appendChild(txn);
            tag.appendChild(remove);
            listDiv.appendChild(tag);
            updateHidden();
        }

        // Initialize from existing value
        if (textarea.value) {
            textarea.value.split(',').forEach(item => addTag(item));
        }

        // Events
        btn.onclick = function () {
            addTag(input.value);
            input.value = '';
            input.focus();
        };

        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent form submission
                addTag(input.value);
                input.value = '';
            }
        });
    }

    // Apply to existing elements
    // The field name ends with 'skills_list'
    document.querySelectorAll('textarea[name$="skills_list"]').forEach(initSkillTags);

    // Observer for dynamically added rows (Django Admin Inlines)
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
                if (node.nodeType === 1) { // ELEMENT_NODE
                    // If the node itself is the textarea (unlikely)
                    if (node.matches && node.matches('textarea[name$="skills_list"]')) {
                        initSkillTags(node);
                    }
                    // If the node contains the textarea
                    const textareas = node.querySelectorAll('textarea[name$="skills_list"]');
                    textareas.forEach(initSkillTags);
                }
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
