import vue from '@vitejs/plugin-vue'
export default { plugins:[vue()], server:{host:'127.0.0.1',port:4185,strictPort:true,fs:{allow:['/Users/scotty/Documents/ChatGPT/DocOfHome']},proxy:{'/api':{target:'http://127.0.0.1:4186'}}}}
