#include "Profile_Data_Processor.h"

#include "LevelEditor.h"
#include "ToolMenus.h"

// Slate UI
#include "Widgets/SCompoundWidget.h"
//#include "Widgets/Layout/SVerticalBox.h"
#include "Widgets/Input/SButton.h"

// System
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Interfaces/IPluginManager.h"

#define LOCTEXT_NAMESPACE "FProfile_Data_ProcessorModule"



class SProfileDataWindow : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SProfileDataWindow) {}
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs)
    {
        ChildSlot
            [
                SNew(SVerticalBox)

                    + SVerticalBox::Slot()
                    .Padding(10)
                    .AutoHeight()
                    .HAlign(HAlign_Center)
                    [
                        SNew(SButton)
                            .HAlign(HAlign_Center)
                            .VAlign(VAlign_Center)
                            .ContentPadding(FMargin(10))
                            [
                                SNew(STextBlock)
                                    .Text(FText::FromString("Start"))
                                    .Justification(ETextJustify::Center)
                            ]
                            .OnClicked(this, &SProfileDataWindow::OnStartClicked)
                    ]

                    + SVerticalBox::Slot()
                    .Padding(10)
                    .AutoHeight()
                    .HAlign(HAlign_Center)
                    [
                        SNew(SButton)
                            .HAlign(HAlign_Center)
                            .VAlign(VAlign_Center)
                            .ContentPadding(FMargin(10))
                            [
                                SNew(STextBlock)
                                    .Text(FText::FromString("Stop and Launch PDPClient"))
                                    .Justification(ETextJustify::Center)
                            ]
                            .OnClicked(this, &SProfileDataWindow::OnStopClicked)
                    ]
            ];
    }

private:

    FReply OnStartClicked()
    {
        if (GEngine)
        {
            GEngine->Exec(nullptr, TEXT("CsvProfile Start"));
        }
        return FReply::Handled();
    }

    FReply OnStopClicked()
    {
        if (GEngine)
        {
            GEngine->Exec(nullptr, TEXT("CsvProfile Stop"));
        }

        // Get plugin directory safely
        TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("Profile_Data_Processor");
        if (!Plugin.IsValid())
        {
            return FReply::Handled();
        }

        FString PluginDir = Plugin->GetBaseDir();
        FString PythonScript = FPaths::Combine(PluginDir, TEXT("Scripts"), TEXT("PDPC.py"));

        FString PythonExe = TEXT("python");
        FString Args = FString::Printf(TEXT("\"%s\""), *PythonScript);

        FPlatformProcess::CreateProc(
            *PythonExe,
            *Args,
            true,
            false,
            false,
            nullptr,
            0,
            nullptr,
            nullptr
        );

        return FReply::Handled();
    }
};




void FProfile_Data_ProcessorModule::StartupModule()
{
    UToolMenus::RegisterStartupCallback(
        FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FProfile_Data_ProcessorModule::RegisterMenus)
    );
}

void FProfile_Data_ProcessorModule::ShutdownModule()
{
    UToolMenus::UnRegisterStartupCallback(this);
    UToolMenus::UnregisterOwner(this);
}

void FProfile_Data_ProcessorModule::RegisterMenus()
{
    FToolMenuOwnerScoped OwnerScoped(this);

    UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");

    FToolMenuSection& Section = Menu->AddSection("ProfileDataProcessor", LOCTEXT("Section", "Profile Tools"));

    Section.AddMenuEntry(
        "OpenPDPWindow",
        LOCTEXT("OpenWindow", "Profile Data Processor"),
        LOCTEXT("Tooltip", "Open Profile Data Capture Window"),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateRaw(this, &FProfile_Data_ProcessorModule::PluginButtonClicked))
    );
}

void FProfile_Data_ProcessorModule::PluginButtonClicked()
{
    TSharedRef<SWindow> Window = SNew(SWindow)
        .Title(FText::FromString("Profile Data Capture"))
        .ClientSize(FVector2D(300, 120))
        .SupportsMinimize(false)
        .SupportsMaximize(false);

    Window->SetContent(SNew(SProfileDataWindow));

    FSlateApplication::Get().AddWindow(Window);
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FProfile_Data_ProcessorModule, Profile_Data_Processor)