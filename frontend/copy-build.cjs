const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'dist');
const targets = [
  path.join(__dirname, '..', 'backend', 'static'),
  path.join(__dirname, '..', 'submission_frontend', 'static')
];

function deleteFolderRecursive(directoryPath) {
  if (fs.existsSync(directoryPath)) {
    fs.readdirSync(directoryPath).forEach((file) => {
      const curPath = path.join(directoryPath, file);
      if (fs.lstatSync(curPath).isDirectory()) {
        deleteFolderRecursive(curPath);
      } else {
        fs.unlinkSync(curPath);
      }
    });
    fs.rmdirSync(directoryPath);
  }
}

function copyFolderRecursive(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  
  fs.readdirSync(src).forEach((file) => {
    const srcPath = path.join(src, file);
    const destPath = path.join(dest, file);
    
    if (fs.lstatSync(srcPath).isDirectory()) {
      copyFolderRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  });
}

console.log('Distributing built assets...');
if (!fs.existsSync(srcDir)) {
  console.error(`Source directory ${srcDir} does not exist. Make sure Vite build completed.`);
  process.exit(1);
}

targets.forEach((target) => {
  console.log(`Copying to ${target}...`);
  if (fs.existsSync(target)) {
    fs.readdirSync(target).forEach((file) => {
      const curPath = path.join(target, file);
      if (fs.lstatSync(curPath).isDirectory()) {
        deleteFolderRecursive(curPath);
      } else {
        fs.unlinkSync(curPath);
      }
    });
  } else {
    fs.mkdirSync(target, { recursive: true });
  }
  
  copyFolderRecursive(srcDir, target);
});

console.log('Distribution complete.');
