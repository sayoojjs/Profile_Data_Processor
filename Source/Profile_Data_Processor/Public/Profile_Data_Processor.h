#pragma once

#include "Modules/ModuleManager.h"

class FProfile_Data_ProcessorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

private:
    void PluginButtonClicked();
    void RegisterMenus();
};