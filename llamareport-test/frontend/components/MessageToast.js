// 消息提示组件
(function() {
    'use strict';
    
    if (typeof window === 'undefined') return;
    
    if (!window.Components) {
        window.Components = {};
    }
    
    window.Components.MessageToast = {
        props: ['message'],
        template: `
            <transition name="fade">
                <div v-if="message.text" :class="['message-toast', message.type]">{{ message.text }}</div>
            </transition>
        `
    };
    
    console.log('✅ MessageToast组件已加载');
})();

