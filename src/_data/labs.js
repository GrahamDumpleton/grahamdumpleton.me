const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

module.exports = function() {
    const labsDir = path.join(__dirname, 'labs');

    // Load the courses index
    const coursesFile = path.join(labsDir, 'courses.yaml');
    const coursesData = yaml.load(fs.readFileSync(coursesFile, 'utf8'));

    // Load each module file referenced by courses
    const modules = {};
    for (const course of coursesData.courses) {
        for (const mod of course.modules) {
            if (mod.file && !modules[mod.file]) {
                const modFile = path.join(labsDir, `${mod.file}.yaml`);
                if (fs.existsSync(modFile)) {
                    modules[mod.file] = yaml.load(fs.readFileSync(modFile, 'utf8'));
                }
            }
        }
    }

    return {
        portal_url: coursesData.portal_url,
        courses: coursesData.courses,
        modules: modules
    };
};
